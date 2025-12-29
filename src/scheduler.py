"""
Email Scheduler

Persists emails for future delivery using SQLite.
Jobs survive restarts and can be managed through the CLI.
"""

import sqlite3
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .email_sender import Email
from .logger import get_logger


class JobStatus(Enum):
    """Status of a scheduled job."""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledJob:
    """A scheduled email job."""
    id: Optional[int]
    recipient: str
    subject: str
    body_html: Optional[str]
    body_text: Optional[str]
    cc: List[str]
    bcc: List[str]
    attachments: List[str]
    scheduled_time: datetime
    status: JobStatus = JobStatus.PENDING
    retry_count: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_email(self) -> Email:
        """Convert to an Email object for sending."""
        return Email(
            to=self.recipient,
            subject=self.subject,
            body_html=self.body_html,
            body_text=self.body_text,
            cc=self.cc,
            bcc=self.bcc,
            attachments=self.attachments
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            "id": self.id,
            "recipient": self.recipient,
            "subject": self.subject,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "error_message": self.error_message
        }


class Scheduler:
    """
    Manages scheduled email jobs with SQLite persistence.
    
    Jobs are stored in a local database and can be processed
    by running the scheduler daemon.
    
    Usage:
        scheduler = Scheduler("./data/jobs.db")
        
        # Schedule an email
        job_id = scheduler.schedule(
            email=email,
            scheduled_time=tomorrow_9am
        )
        
        # List scheduled jobs
        jobs = scheduler.list_pending()
        
        # Cancel a job
        scheduler.cancel(job_id)
    """
    
    def __init__(self, db_path: str = "./data/scheduled-jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger()
        self._lock = threading.Lock()
        
        self._init_database()
    
    def _init_database(self):
        """Create the jobs table if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body_html TEXT,
                    body_text TEXT,
                    cc TEXT,
                    bcc TEXT,
                    attachments TEXT,
                    scheduled_time TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_status_time 
                ON scheduled_jobs(status, scheduled_time)
            """)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def schedule(self, email: Email, scheduled_time: datetime) -> int:
        """
        Schedule an email for future delivery.
        
        Returns the job ID.
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO scheduled_jobs 
                    (recipient, subject, body_html, body_text, cc, bcc, attachments, scheduled_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email.to,
                    email.subject,
                    email.body_html,
                    email.body_text,
                    json.dumps(email.cc),
                    json.dumps(email.bcc),
                    json.dumps(email.attachments),
                    scheduled_time.isoformat()
                ))
                
                job_id = cursor.lastrowid
                self.logger.info(
                    f"Scheduled email to {email.to} for {scheduled_time.isoformat()}",
                    job_id=job_id
                )
                return job_id
    
    def get_job(self, job_id: int) -> Optional[ScheduledJob]:
        """Get a specific job by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM scheduled_jobs WHERE id = ?",
                (job_id,)
            ).fetchone()
            
            if row:
                return self._row_to_job(row)
            return None
    
    def list_pending(self) -> List[ScheduledJob]:
        """Get all pending jobs."""
        return self._list_by_status(JobStatus.PENDING)
    
    def list_due(self) -> List[ScheduledJob]:
        """Get pending jobs that are due for sending (scheduled time has passed)."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM scheduled_jobs 
                WHERE status = 'pending' AND scheduled_time <= ?
                ORDER BY scheduled_time ASC
            """, (now,)).fetchall()
            
            return [self._row_to_job(row) for row in rows]
    
    def list_all(self, limit: int = 50) -> List[ScheduledJob]:
        """Get all jobs, most recent first."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM scheduled_jobs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [self._row_to_job(row) for row in rows]
    
    def _list_by_status(self, status: JobStatus) -> List[ScheduledJob]:
        """Get jobs with a specific status."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_jobs WHERE status = ? ORDER BY scheduled_time ASC",
                (status.value,)
            ).fetchall()
            
            return [self._row_to_job(row) for row in rows]
    
    def update_status(
        self,
        job_id: int,
        status: JobStatus,
        error_message: Optional[str] = None
    ):
        """Update the status of a job."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE scheduled_jobs 
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status.value, error_message, job_id))
    
    def mark_sent(self, job_id: int):
        """Mark a job as successfully sent."""
        self.update_status(job_id, JobStatus.SENT)
        self.logger.success(f"Job {job_id} marked as sent")
    
    def mark_failed(self, job_id: int, error_message: str):
        """Mark a job as failed."""
        self.update_status(job_id, JobStatus.FAILED, error_message)
        self.logger.error(f"Job {job_id} marked as failed: {error_message}")
    
    def increment_retry(self, job_id: int):
        """Increment the retry counter for a job."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE scheduled_jobs 
                    SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (job_id,))
    
    def cancel(self, job_id: int) -> bool:
        """
        Cancel a pending job.
        
        Returns True if the job was cancelled, False if it couldn't be.
        """
        job = self.get_job(job_id)
        
        if not job:
            return False
        
        if job.status not in (JobStatus.PENDING, JobStatus.PROCESSING):
            return False  # Can only cancel pending or processing jobs
        
        self.update_status(job_id, JobStatus.CANCELLED)
        self.logger.info(f"Cancelled job {job_id}")
        return True
    
    def reschedule(self, job_id: int, new_time: datetime) -> bool:
        """Reschedule a job for a different time."""
        job = self.get_job(job_id)
        
        if not job or job.status != JobStatus.PENDING:
            return False
        
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE scheduled_jobs 
                    SET scheduled_time = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_time.isoformat(), job_id))
        
        self.logger.info(f"Rescheduled job {job_id} to {new_time.isoformat()}")
        return True
    
    def cleanup_old_jobs(self, days: int = 30):
        """Remove completed jobs older than the specified days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._lock:
            with self._get_connection() as conn:
                result = conn.execute("""
                    DELETE FROM scheduled_jobs 
                    WHERE status IN ('sent', 'cancelled', 'failed') 
                    AND updated_at < ?
                """, (cutoff,))
                
                deleted = result.rowcount
                if deleted > 0:
                    self.logger.info(f"Cleaned up {deleted} old jobs")
    
    def get_stats(self) -> Dict[str, int]:
        """Get counts by status."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM scheduled_jobs 
                GROUP BY status
            """).fetchall()
            
            return {row['status']: row['count'] for row in rows}
    
    def _row_to_job(self, row: sqlite3.Row) -> ScheduledJob:
        """Convert a database row to a ScheduledJob object."""
        return ScheduledJob(
            id=row['id'],
            recipient=row['recipient'],
            subject=row['subject'],
            body_html=row['body_html'],
            body_text=row['body_text'],
            cc=json.loads(row['cc'] or '[]'),
            bcc=json.loads(row['bcc'] or '[]'),
            attachments=json.loads(row['attachments'] or '[]'),
            scheduled_time=datetime.fromisoformat(row['scheduled_time']),
            status=JobStatus(row['status']),
            retry_count=row['retry_count'],
            error_message=row['error_message'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )


# Default scheduler instance
_scheduler: Optional[Scheduler] = None


def get_scheduler(db_path: Optional[str] = None) -> Scheduler:
    """Get or create the default scheduler."""
    global _scheduler
    if _scheduler is None or db_path is not None:
        _scheduler = Scheduler(db_path or "./data/scheduled-jobs.db")
    return _scheduler
