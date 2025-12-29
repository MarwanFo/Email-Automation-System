"""
Beautiful Output Formatters

Using Rich to make terminal output actually enjoyable.
Because staring at plain text gets old fast.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text
from rich import box

from .colors import SUCCESS, ERROR, WARNING, INFO, ACCENT


# Global console instance — we use one everywhere for consistency
console = Console()


def print_banner():
    """
    Display the welcome banner with ASCII art.
    
    We only show this on first run or explicit request to keep
    the interface clean during regular use.
    """
    banner = """
  ╔═══════════════════════════════════════╗
  ║                                       ║
  ║     📧  A U T O M A T I O N          ║
  ║          M  A  I  L                   ║
  ║                                       ║
  ║     Send smarter, not harder          ║
  ║                                       ║
  ╚═══════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def print_logo_small():
    """Compact logo for regular command output."""
    console.print("\n📧 [bold]Automation Mail[/bold]\n", style="blue")


def print_status(message: str, status_type: str = "info"):
    """
    Print a status message with appropriate styling.
    
    status_type: 'info', 'success', 'warning', 'error'
    """
    styles = {
        "info": ("blue", "ℹ"),
        "success": ("green", "✓"),
        "warning": ("yellow", "⚠"),
        "error": ("red", "✗"),
    }
    color, icon = styles.get(status_type, ("white", "•"))
    console.print(f"  {icon} {message}", style=color)


def print_success(message: str):
    """Print a success message with celebration."""
    console.print(f"\n✨ {message}\n", style="bold green")


def print_error(message: str):
    """Print an error message without being scary."""
    console.print(f"\n{message}", style="red")


def print_warning(message: str):
    """Print a warning that draws attention but doesn't alarm."""
    console.print(f"\n⚠  {message}\n", style="yellow")


def print_info(message: str):
    """Print helpful information."""
    console.print(f"\n💡 {message}\n", style="blue")


def print_email_preview(
    to: str,
    subject: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None
):
    """
    Show a nicely formatted preview of an email before sending.
    
    This gives users a chance to spot mistakes before committing.
    """
    console.print()
    console.print(f"  [bold]To:[/bold] {to}")
    
    if cc:
        console.print(f"  [bold]CC:[/bold] {', '.join(cc)}")
    
    if bcc:
        console.print(f"  [bold]BCC:[/bold] {', '.join(bcc)}")
    
    console.print(f"  [bold]Subject:[/bold] {subject}")
    
    if attachments:
        console.print(f"  [bold]Attachments:[/bold] {len(attachments)} file(s)")
        for attachment in attachments:
            filename = Path(attachment).name
            console.print(f"    📎 {filename}", style="dim")
    
    console.print()


def create_progress_bar(description: str = "Processing...", total: int = 100) -> Progress:
    """
    Create a beautiful progress bar for long operations.
    
    Returns a Progress context manager that you use like:
    
        with create_progress_bar("Sending emails", total=100) as progress:
            task = progress.add_task("", total=100)
            for item in items:
                do_work(item)
                progress.update(task, advance=1)
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    )


def print_bulk_summary(stats: Dict[str, int]):
    """
    Pretty-print the summary of a bulk send operation.
    
    stats should have keys: 'sent', 'failed', 'retrying'
    """
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  [green]✓[/green] {stats.get('sent', 0)} sent")
    
    if stats.get('retrying', 0) > 0:
        console.print(f"  [yellow]⚠[/yellow] {stats['retrying']} retrying")
    
    if stats.get('failed', 0) > 0:
        console.print(f"  [red]✗[/red] {stats['failed']} failed")
    
    console.print()


def print_recipients_table(recipients: List[Dict[str, Any]], limit: int = 10):
    """
    Show a preview table of recipients from a CSV.
    
    This helps users verify they're about to email the right people.
    """
    table = Table(title="Recipients Preview", box=box.ROUNDED)
    
    if not recipients:
        console.print("  No recipients found.", style="dim")
        return
    
    # Get column headers from first recipient
    headers = list(recipients[0].keys())
    for header in headers[:5]:  # Limit columns for readability
        table.add_column(header.replace("_", " ").title())
    
    # Add rows (limited preview)
    for recipient in recipients[:limit]:
        row = [str(recipient.get(h, ""))[:30] for h in headers[:5]]
        table.add_row(*row)
    
    if len(recipients) > limit:
        table.add_row(*["..." for _ in headers[:5]])
    
    console.print(table)
    console.print(f"  Total: {len(recipients)} recipients\n", style="dim")


def print_scheduled_jobs_table(jobs: List[Dict[str, Any]]):
    """Display scheduled jobs in a nice table format."""
    table = Table(title="Scheduled Emails", box=box.ROUNDED)
    
    table.add_column("ID", style="dim")
    table.add_column("To")
    table.add_column("Subject")
    table.add_column("Scheduled For")
    table.add_column("Status")
    
    for job in jobs:
        status_style = {
            "pending": "yellow",
            "sent": "green",
            "failed": "red",
        }.get(job.get("status", "pending"), "white")
        
        table.add_row(
            str(job.get("id", ""))[:8],
            job.get("recipient", "")[:25],
            job.get("subject", "")[:30],
            job.get("scheduled_time", ""),
            f"[{status_style}]{job.get('status', 'pending')}[/{status_style}]"
        )
    
    console.print(table)


def print_config_summary(config: Dict[str, Any]):
    """Show current configuration in a readable format."""
    console.print("\n[bold]Current Configuration:[/bold]\n")
    
    # SMTP settings (hide password)
    console.print("  [bold]SMTP Settings[/bold]")
    console.print(f"    Host: {config.get('smtp_host', 'not set')}")
    console.print(f"    Port: {config.get('smtp_port', 'not set')}")
    console.print(f"    Username: {config.get('smtp_username', 'not set')}")
    console.print(f"    Password: {'••••••••' if config.get('smtp_password') else 'not set'}")
    console.print(f"    TLS: {'enabled' if config.get('smtp_use_tls') else 'disabled'}")
    
    console.print()
    console.print("  [bold]Sender Identity[/bold]")
    console.print(f"    Name: {config.get('sender_name', 'not set')}")
    console.print(f"    Email: {config.get('sender_email', 'not set')}")
    
    console.print()
    console.print("  [bold]Rate Limiting[/bold]")
    console.print(f"    Emails/minute: {config.get('rate_limit', 8)}")
    console.print(f"    Max retries: {config.get('max_retries', 3)}")
    
    console.print()


def clear_screen():
    """Clear the terminal screen for a fresh start."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_divider(char: str = "─", width: int = 50):
    """Print a subtle divider line."""
    console.print(char * width, style="dim")
