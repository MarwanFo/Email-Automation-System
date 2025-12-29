"""
Tests for the Scheduler module.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scheduler import Scheduler, ScheduledJob, JobStatus
from src.email_sender import Email


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def scheduler(tmp_path):
    """Create a scheduler with a temporary database."""
    db_path = tmp_path / "test_jobs.db"
    return Scheduler(str(db_path))


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        to="test@example.com",
        subject="Test Subject",
        body_text="Test body content",
        body_html="<p>Test body content</p>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduling Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestScheduling:
    """Tests for scheduling emails."""
    
    def test_schedule_email(self, scheduler, sample_email):
        """Should schedule an email and return a job ID."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        assert job_id is not None
        assert isinstance(job_id, int)
        assert job_id > 0
    
    def test_get_scheduled_job(self, scheduler, sample_email):
        """Should retrieve a scheduled job by ID."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        job = scheduler.get_job(job_id)
        
        assert job is not None
        assert job.id == job_id
        assert job.recipient == "test@example.com"
        assert job.subject == "Test Subject"
        assert job.status == JobStatus.PENDING
    
    def test_convert_job_to_email(self, scheduler, sample_email):
        """Should convert scheduled job back to Email object."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        job = scheduler.get_job(job_id)
        email = job.to_email()
        
        assert email.to == sample_email.to
        assert email.subject == sample_email.subject
        assert email.body_text == sample_email.body_text
    
    def test_nonexistent_job_returns_none(self, scheduler):
        """Should return None for nonexistent job ID."""
        job = scheduler.get_job(99999)
        assert job is None


# ═══════════════════════════════════════════════════════════════════════════════
# Listing Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestListing:
    """Tests for listing scheduled jobs."""
    
    def test_list_pending(self, scheduler, sample_email):
        """Should list pending jobs."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        scheduler.schedule(sample_email, scheduled_time)
        scheduler.schedule(sample_email, scheduled_time)
        
        pending = scheduler.list_pending()
        
        assert len(pending) == 2
        assert all(job.status == JobStatus.PENDING for job in pending)
    
    def test_list_due_jobs(self, scheduler):
        """Should list jobs that are due for sending."""
        past_time = datetime.now() - timedelta(minutes=5)
        future_time = datetime.now() + timedelta(hours=1)
        
        past_email = Email(to="past@example.com", subject="Past", body_text="Due now")
        future_email = Email(to="future@example.com", subject="Future", body_text="Later")
        
        scheduler.schedule(past_email, past_time)
        scheduler.schedule(future_email, future_time)
        
        due = scheduler.list_due()
        
        assert len(due) == 1
        assert due[0].recipient == "past@example.com"
    
    def test_list_all_jobs(self, scheduler, sample_email):
        """Should list all jobs regardless of status."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        # Mark one as sent
        scheduler.mark_sent(job_id)
        
        # Schedule another
        scheduler.schedule(sample_email, scheduled_time)
        
        all_jobs = scheduler.list_all()
        
        assert len(all_jobs) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Status Update Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatusUpdates:
    """Tests for updating job statuses."""
    
    def test_mark_sent(self, scheduler, sample_email):
        """Should mark a job as sent."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        scheduler.mark_sent(job_id)
        
        job = scheduler.get_job(job_id)
        assert job.status == JobStatus.SENT
    
    def test_mark_failed(self, scheduler, sample_email):
        """Should mark a job as failed with error message."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        scheduler.mark_failed(job_id, "Connection refused")
        
        job = scheduler.get_job(job_id)
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Connection refused"
    
    def test_increment_retry(self, scheduler, sample_email):
        """Should increment retry counter."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        scheduler.increment_retry(job_id)
        scheduler.increment_retry(job_id)
        
        job = scheduler.get_job(job_id)
        assert job.retry_count == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Cancel and Reschedule Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCancelAndReschedule:
    """Tests for cancelling and rescheduling jobs."""
    
    def test_cancel_pending_job(self, scheduler, sample_email):
        """Should cancel a pending job."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        result = scheduler.cancel(job_id)
        
        assert result is True
        job = scheduler.get_job(job_id)
        assert job.status == JobStatus.CANCELLED
    
    def test_cannot_cancel_sent_job(self, scheduler, sample_email):
        """Should not cancel already sent jobs."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        scheduler.mark_sent(job_id)
        
        result = scheduler.cancel(job_id)
        
        assert result is False
    
    def test_cancel_nonexistent_job(self, scheduler):
        """Should return False for nonexistent job."""
        result = scheduler.cancel(99999)
        assert result is False
    
    def test_reschedule_job(self, scheduler, sample_email):
        """Should reschedule a pending job."""
        original_time = datetime.now() + timedelta(hours=1)
        new_time = datetime.now() + timedelta(hours=2)
        
        job_id = scheduler.schedule(sample_email, original_time)
        result = scheduler.reschedule(job_id, new_time)
        
        assert result is True
        job = scheduler.get_job(job_id)
        assert job.scheduled_time == new_time


# ═══════════════════════════════════════════════════════════════════════════════
# Stats Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStats:
    """Tests for job statistics."""
    
    def test_get_stats(self, scheduler, sample_email):
        """Should return job counts by status."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Schedule 3 jobs
        job1 = scheduler.schedule(sample_email, scheduled_time)
        job2 = scheduler.schedule(sample_email, scheduled_time)
        job3 = scheduler.schedule(sample_email, scheduled_time)
        
        # Mark one as sent, one as failed
        scheduler.mark_sent(job1)
        scheduler.mark_failed(job2, "Error")
        
        stats = scheduler.get_stats()
        
        assert stats.get("sent", 0) == 1
        assert stats.get("failed", 0) == 1
        assert stats.get("pending", 0) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# ScheduledJob Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestScheduledJob:
    """Tests for the ScheduledJob dataclass."""
    
    def test_to_dict(self, scheduler, sample_email):
        """Should convert job to dictionary."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job_id = scheduler.schedule(sample_email, scheduled_time)
        
        job = scheduler.get_job(job_id)
        job_dict = job.to_dict()
        
        assert job_dict["recipient"] == "test@example.com"
        assert job_dict["subject"] == "Test Subject"
        assert job_dict["status"] == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
