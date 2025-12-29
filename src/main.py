"""
Automation Mail CLI

The command-line interface that brings everything together.
We've put a lot of thought into making this feel like a
conversation, not a form to fill out.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import click
from rich.prompt import Prompt, Confirm

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import __version__
from src.config import load_config, get_default_config_template, ConfigurationError
from src.email_sender import EmailSender, Email
from src.template_engine import TemplateEngine, TemplateError
from src.scheduler import Scheduler, get_scheduler
from src.validator import EmailValidator, CSVValidator
from src.logger import setup_logger, get_logger, EmailLog
from src.utils import parse_datetime, format_duration
from src.ui.formatters import (
    console, print_banner, print_status, print_error, print_success,
    print_email_preview, print_bulk_summary, print_recipients_table,
    print_scheduled_jobs_table, print_config_summary, create_progress_bar,
    print_logo_small, print_warning, print_info
)
from src.ui.messages import Messages


# Click context settings for better help formatting
CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    max_content_width=88
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name='Automation Mail')
@click.pass_context
def cli(ctx):
    """
    📧 Automation Mail — Send smarter, not harder
    
    A thoughtfully designed email automation tool for humans.
    
    \b
    Quick Start:
      automation-mail configure        Set up your email account
      automation-mail send             Send a single email
      automation-mail bulk             Send to multiple recipients
      automation-mail schedule         Schedule for later
    
    \b
    Examples:
      # Send a quick email
      automation-mail send --to sarah@studio.io --subject "Coffee?"
      
      # Send newsletter to your list
      automation-mail bulk --recipients clients.csv --template newsletter.html
      
      # Schedule a reminder
      automation-mail schedule --to team@company.com --subject "Meeting tomorrow" --when "tomorrow 9am"
    
    \b
    Need help? Check the docs at: docs/USER_GUIDE.md
    """
    ctx.ensure_object(dict)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURE COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--show', is_flag=True, help='Show current configuration')
def configure(show):
    """
    Set up your email account (interactive wizard)
    
    We'll walk you through connecting your email provider.
    Takes about 2 minutes.
    """
    print_banner()
    
    if show:
        try:
            config = load_config()
            print_config_summary(config.to_dict())
        except ConfigurationError:
            print_warning("No configuration found yet. Run 'automation-mail configure' to set up.")
        return
    
    console.print("\n[bold]Let's set up your email![/bold]\n")
    console.print("We'll create a .env file with your settings.\n")
    
    # Check if .env already exists
    env_path = Path(".env")
    if env_path.exists():
        if not Confirm.ask("A .env file already exists. Overwrite it?"):
            console.print("\n👍 Keeping your existing configuration.")
            return
    
    # Collect settings interactively
    console.print("\n[bold]SMTP Settings[/bold]")
    console.print("These connect us to your email provider.\n")
    
    # Provider selection
    provider = Prompt.ask(
        "Which email provider",
        choices=["gmail", "outlook", "custom"],
        default="gmail"
    )
    
    if provider == "gmail":
        smtp_host = "smtp.gmail.com"
        smtp_port = "587"
        console.print("\n💡 [dim]For Gmail, you'll need an App Password.[/dim]")
        console.print("[dim]   Get one at: https://myaccount.google.com/apppasswords[/dim]\n")
    elif provider == "outlook":
        smtp_host = "smtp.office365.com"
        smtp_port = "587"
        console.print("\n💡 [dim]For Outlook, you may need to enable SMTP in settings.[/dim]\n")
    else:
        smtp_host = Prompt.ask("SMTP host", default="smtp.example.com")
        smtp_port = Prompt.ask("SMTP port", default="587")
    
    email = Prompt.ask("Your email address")
    password = Prompt.ask("App password (not your regular password)", password=True)
    name = Prompt.ask("Your name (as it appears to recipients)", default=email.split("@")[0].title())
    
    # Create the .env file
    env_content = f"""# ========================================
# 📧 Automation Mail Configuration
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
# ========================================

# SMTP Settings
SMTP_HOST={smtp_host}
SMTP_PORT={smtp_port}
SMTP_USERNAME={email}
SMTP_PASSWORD={password}
SMTP_USE_TLS=true

# Sender Identity
SENDER_NAME={name}
SENDER_EMAIL={email}
REPLY_TO_EMAIL={email}

# Sending Behavior
RATE_LIMIT_EMAILS_PER_MINUTE=8
MAX_RETRIES=3
RETRY_DELAY_SECONDS=60

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/automation-mail.log

# Scheduling
SCHEDULER_TIMEZONE=UTC
JOB_PERSISTENCE_PATH=./data/scheduled-jobs.db
"""
    
    env_path.write_text(env_content, encoding='utf-8')
    
    print_success("Configuration saved to .env")
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Test your connection:  [cyan]automation-mail test-connection[/cyan]")
    console.print("  2. Send a test email:     [cyan]automation-mail send --to your@email.com --subject \"Test\"[/cyan]")
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CONNECTION COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command('test-connection')
def test_connection():
    """
    Test your SMTP connection
    
    Verifies that we can connect to your email provider without
    actually sending anything.
    """
    print_logo_small()
    console.print(Messages.testing_connection())
    
    try:
        config = load_config()
    except ConfigurationError as e:
        print_error(str(e))
        console.print("\n💡 Run [cyan]automation-mail configure[/cyan] to set up your account.")
        sys.exit(1)
    
    sender = EmailSender(config)
    success, message = sender.test_connection()
    
    if success:
        print_success(message)
        console.print("You're ready to send emails! 🚀\n")
    else:
        print_error(message)
        console.print("\n💡 Try [cyan]automation-mail troubleshoot[/cyan] for help.\n")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# SEND COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('-t', '--to', 'recipient', required=True, help='Recipient email address')
@click.option('-s', '--subject', required=True, help='Email subject line')
@click.option('-b', '--body', help='Email body (plain text)')
@click.option('--html', 'body_html', help='Email body (HTML)')
@click.option('--template', 'template_path', type=click.Path(exists=True), help='Path to template file')
@click.option('-a', '--attach', 'attachments', multiple=True, type=click.Path(exists=True), help='Attach a file')
@click.option('--cc', multiple=True, help='CC recipients')
@click.option('--bcc', multiple=True, help='BCC recipients')
@click.option('--dry-run', is_flag=True, help='Preview without sending')
def send(recipient, subject, body, body_html, template_path, attachments, cc, bcc, dry_run):
    """
    Send a single email right now
    
    \b
    Examples:
      # Simple email
      automation-mail send -t friend@email.com -s "Hello!" -b "How are you?"
      
      # With template
      automation-mail send -t client@co.com -s "Proposal" --template proposal.html
      
      # With attachments
      automation-mail send -t boss@work.com -s "Report" -a report.pdf -a data.xlsx
    """
    print_logo_small()
    
    # Validate recipient
    validation = EmailValidator.validate(recipient)
    if not validation.is_valid:
        print_error(Messages.invalid_email(recipient))
        sys.exit(1)
    
    # Load config
    try:
        config = load_config()
    except ConfigurationError as e:
        print_error(str(e))
        sys.exit(1)
    
    # Resolve body content
    if template_path:
        console.print(Messages.loading_template(template_path))
        try:
            engine = TemplateEngine()
            rendered = engine.render_file(template_path, {})
            body_html = rendered.body_html
            body = rendered.body_text
        except TemplateError as e:
            print_error(f"Template error: {e}")
            sys.exit(1)
    
    if not body and not body_html:
        print_error("Please provide a message body with --body, --html, or --template")
        sys.exit(1)
    
    # Show preview
    console.print(Messages.preparing_email())
    print_email_preview(
        to=recipient,
        subject=subject,
        cc=list(cc) if cc else None,
        bcc=list(bcc) if bcc else None,
        attachments=list(attachments) if attachments else None
    )
    
    if dry_run:
        console.print("[yellow]Dry run mode — email not sent[/yellow]\n")
        return
    
    # Create and send the email
    email = Email(
        to=recipient,
        subject=subject,
        body_html=body_html,
        body_text=body or "This email was sent from Automation Mail.",
        cc=list(cc),
        bcc=list(bcc),
        attachments=list(attachments)
    )
    
    with EmailSender(config) as sender:
        result = sender.send(email)
    
    if result.success:
        console.print(Messages.email_sent(recipient))
        if result.message_id:
            console.print(f"  Message ID: [dim]{result.message_id}[/dim]\n")
    else:
        print_error(f"Failed to send: {result.error_message}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# BULK COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('-r', '--recipients', required=True, type=click.Path(exists=True), help='CSV file with recipients')
@click.option('-t', '--template', 'template_path', required=True, type=click.Path(exists=True), help='Email template')
@click.option('-s', '--subject', required=True, help='Email subject (can use {{variables}})')
@click.option('--preview', is_flag=True, help='Preview without sending')
@click.option('--limit', type=int, help='Only send to first N recipients (for testing)')
def bulk(recipients, template_path, subject, preview, limit):
    """
    Send to multiple recipients from a CSV file
    
    \b
    Your CSV should have at least an 'email' column:
      email,first_name,company
      maya@studio.io,Maya,Design Studio
      james@tech.co,James,TechForge
    
    \b
    Templates can use {{variable}} syntax:
      Hey {{first_name}}! Your company {{company}} rocks.
    
    \b
    Examples:
      automation-mail bulk -r clients.csv -t newsletter.html -s "Monthly Update"
      automation-mail bulk -r leads.csv -t welcome.html -s "Welcome {{first_name}}!" --preview
    """
    print_logo_small()
    
    # Validate CSV file
    csv_validation = CSVValidator.validate(recipients)
    if not csv_validation.is_valid:
        print_error(csv_validation.message)
        sys.exit(1)
    
    # Load recipients
    console.print(Messages.reading_recipients(recipients))
    recipient_list, errors = CSVValidator.load_recipients(recipients)
    
    if errors:
        console.print(f"\n[yellow]Found {len(errors)} invalid rows:[/yellow]")
        for error in errors[:5]:
            console.print(f"  • {error}")
        if len(errors) > 5:
            console.print(f"  ... and {len(errors) - 5} more")
        console.print()
    
    if not recipient_list:
        print_error("No valid recipients found in the CSV file.")
        sys.exit(1)
    
    # Apply limit if specified
    if limit:
        recipient_list = recipient_list[:limit]
        console.print(f"[dim]Limited to first {limit} recipients[/dim]\n")
    
    # Show preview
    print_recipients_table(recipient_list)
    
    if preview:
        console.print("[yellow]Preview mode — no emails sent[/yellow]\n")
        return
    
    # Confirm before sending
    if not Confirm.ask(f"Send to {len(recipient_list)} recipients?"):
        console.print("\n👍 Cancelled. No emails sent.\n")
        return
    
    # Load config and template
    try:
        config = load_config()
    except ConfigurationError as e:
        print_error(str(e))
        sys.exit(1)
    
    console.print(Messages.loading_template(template_path))
    engine = TemplateEngine()
    
    # Send emails with progress bar
    console.print(Messages.sending_bulk(len(recipient_list)))
    console.print()
    
    stats = {"sent": 0, "failed": 0, "retrying": 0}
    email_log = EmailLog("bulk-send")
    start_time = datetime.now()
    
    with EmailSender(config) as sender:
        with create_progress_bar("Sending...", len(recipient_list)) as progress:
            task = progress.add_task("", total=len(recipient_list))
            
            for recipient_data in recipient_list:
                try:
                    # Render template with this recipient's data
                    rendered = engine.render_file(template_path, recipient_data)
                    
                    # Render subject with data too
                    subject_template = engine.render_string(subject, recipient_data)
                    final_subject = subject_template.body_text or subject
                    
                    email = Email(
                        to=recipient_data["email"],
                        subject=final_subject,
                        body_html=rendered.body_html,
                        body_text=rendered.body_text
                    )
                    
                    result = sender.send(email)
                    
                    if result.success:
                        stats["sent"] += 1
                        email_log.add(recipient_data["email"], "sent")
                    else:
                        stats["failed"] += 1
                        email_log.add(recipient_data["email"], "failed", result.error_message)
                    
                except Exception as e:
                    stats["failed"] += 1
                    email_log.add(recipient_data.get("email", "unknown"), "failed", str(e))
                
                progress.update(task, advance=1)
    
    # Save log and show summary
    log_path = email_log.save()
    duration = (datetime.now() - start_time).total_seconds()
    
    print_bulk_summary(stats)
    console.print(Messages.bulk_complete(stats["sent"], stats["failed"], stats.get("retrying", 0)))
    console.print(f"  📋 Detailed log: [cyan]{log_path}[/cyan]\n")
    console.print(f"  ⏱️  Completed in {format_duration(duration)}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULE COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('-t', '--to', 'recipient', required=True, help='Recipient email')
@click.option('-s', '--subject', required=True, help='Email subject')
@click.option('-b', '--body', help='Email body')
@click.option('--template', 'template_path', type=click.Path(exists=True), help='Template file')
@click.option('-w', '--when', 'scheduled_time', required=True, help='When to send (e.g. "tomorrow 9am", "2025-12-30 14:00")')
def schedule(recipient, subject, body, template_path, scheduled_time):
    """
    Schedule an email for later
    
    \b
    Time formats supported:
      "in 2 hours"
      "tomorrow 9am"
      "2025-12-30 14:00"
    
    \b
    Examples:
      automation-mail schedule -t team@co.com -s "Reminder" -b "Don't forget!" -w "tomorrow 9am"
      automation-mail schedule -t client@co.com -s "Follow up" --template followup.html -w "in 3 hours"
    """
    print_logo_small()
    
    # Validate recipient
    validation = EmailValidator.validate(recipient)
    if not validation.is_valid:
        print_error(Messages.invalid_email(recipient))
        sys.exit(1)
    
    # Parse the scheduled time
    dt = parse_datetime(scheduled_time)
    if not dt:
        print_error(f"Couldn't understand the time: '{scheduled_time}'")
        console.print("\n[dim]Try formats like:[/dim]")
        console.print("  • 'tomorrow 9am'")
        console.print("  • 'in 2 hours'")
        console.print("  • '2025-12-30 14:00'\n")
        sys.exit(1)
    
    # Check if time is in the past
    if dt < datetime.now():
        print_error("That time is in the past! Scheduling for the future only.")
        sys.exit(1)
    
    # Resolve body
    body_html = None
    if template_path:
        try:
            engine = TemplateEngine()
            rendered = engine.render_file(template_path, {})
            body_html = rendered.body_html
            body = rendered.body_text
        except TemplateError as e:
            print_error(f"Template error: {e}")
            sys.exit(1)
    
    if not body and not body_html:
        body = Prompt.ask("Enter the email body")
    
    # Create the email and schedule it
    email = Email(
        to=recipient,
        subject=subject,
        body_html=body_html,
        body_text=body or "Sent from Automation Mail"
    )
    
    scheduler = get_scheduler()
    job_id = scheduler.schedule(email, dt)
    
    formatted_time = dt.strftime("%A, %B %d at %I:%M %p")
    console.print(Messages.scheduled(recipient, formatted_time))
    console.print(f"  Job ID: [cyan]{job_id}[/cyan]")
    console.print(f"\n  💡 View scheduled: [cyan]automation-mail list-scheduled[/cyan]\n")


# ═══════════════════════════════════════════════════════════════════════════════
# LIST SCHEDULED COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command('list-scheduled')
@click.option('--all', 'show_all', is_flag=True, help='Show all jobs, not just pending')
def list_scheduled(show_all):
    """
    View your scheduled emails
    """
    print_logo_small()
    
    scheduler = get_scheduler()
    
    if show_all:
        jobs = scheduler.list_all()
    else:
        jobs = scheduler.list_pending()
    
    if not jobs:
        console.print("📭 No scheduled emails.\n")
        console.print("[dim]Schedule one with: automation-mail schedule --help[/dim]\n")
        return
    
    print_scheduled_jobs_table([job.to_dict() for job in jobs])


# ═══════════════════════════════════════════════════════════════════════════════
# CANCEL COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.argument('job_id', type=int)
def cancel(job_id):
    """
    Cancel a scheduled email
    
    Use 'automation-mail list-scheduled' to see job IDs.
    """
    print_logo_small()
    
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    
    if not job:
        print_error(f"Job {job_id} not found.")
        sys.exit(1)
    
    if scheduler.cancel(job_id):
        print_success(f"Cancelled job {job_id} (to {job.recipient})")
    else:
        print_error(f"Couldn't cancel job {job_id}. It may have already been sent.")


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
def templates():
    """
    List available email templates
    """
    print_logo_small()
    
    engine = TemplateEngine()
    available = engine.list_available_templates()
    
    if not available:
        console.print("📁 No templates found in templates/\n")
        console.print("[dim]Create a .html or .txt file in the templates/ directory.[/dim]\n")
        return
    
    console.print("[bold]Available Templates:[/bold]\n")
    
    for template in available:
        console.print(f"  📄 [cyan]{template['name']}[/cyan] ({template['type']})")
        console.print(f"     Path: {template['path']}")
        if template['variables']:
            vars_str = ", ".join(f"{{{{{v}}}}}" for v in template['variables'][:5])
            if len(template['variables']) > 5:
                vars_str += f" ... (+{len(template['variables']) - 5} more)"
            console.print(f"     Variables: {vars_str}")
        console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# TROUBLESHOOT COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
def troubleshoot():
    """
    Diagnose common issues
    """
    print_banner()
    console.print("[bold]Let's figure out what's wrong...[/bold]\n")
    
    issues_found = False
    
    # Check .env file
    console.print("Checking configuration...")
    if not Path(".env").exists():
        print_status("No .env file found", "error")
        console.print("  → Run [cyan]automation-mail configure[/cyan] to set up\n")
        issues_found = True
    else:
        print_status(".env file exists", "success")
        
        try:
            config = load_config()
            print_status("Configuration loaded successfully", "success")
            
            # Test SMTP connection
            console.print("\nTesting SMTP connection...")
            sender = EmailSender(config)
            success, message = sender.test_connection()
            
            if success:
                print_status("SMTP connection works", "success")
            else:
                print_status("SMTP connection failed", "error")
                console.print(f"  → {message}\n")
                issues_found = True
                
        except ConfigurationError as e:
            print_status("Configuration error", "error")
            console.print(f"  → {e}\n")
            issues_found = True
    
    # Check directories
    console.print("\nChecking directories...")
    for dir_name in ["logs", "data", "templates"]:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print_status(f"{dir_name}/ exists", "success")
        else:
            print_status(f"{dir_name}/ missing (will be created when needed)", "warning")
    
    console.print()
    
    if not issues_found:
        print_success("Everything looks good! 🎉")
        console.print("If you're still having issues, check docs/TROUBLESHOOTING.md\n")
    else:
        console.print("[yellow]Fix the issues above and try again.[/yellow]\n")


# ═══════════════════════════════════════════════════════════════════════════════
# HIDDEN EASTER EGG
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command(hidden=True)
def motivate():
    """A little encouragement when you need it"""
    import random
    
    messages = [
        "You're doing great! Those emails are going to make someone's day ✨",
        "Remember: every newsletter you send is content someone chose to receive 📬",
        "You're more organized than 99% of people. Keep going! 💪",
        "That bulk send is going to look so good in your metrics 📊",
        "Coffee break? You've earned it ☕",
        "Fun fact: The first email was sent in 1971. You're part of history! 📜",
        "Your emails are probably better than most CEOs' 💼",
        "Automation Mail believes in you. Now go automate something! 🚀",
    ]
    
    console.print(f"\n{random.choice(messages)}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for the CLI."""
    # Set up logging
    setup_logger()
    
    # Create necessary directories
    for dir_name in ["logs", "data"]:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Run the CLI
    cli()


if __name__ == "__main__":
    main()
