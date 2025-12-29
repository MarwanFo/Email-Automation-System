"""
Human-Crafted Messages

Every message here was written by someone who's been frustrated
by robotic error messages. We believe software should talk to you
like a helpful colleague, not a bureaucratic form letter.
"""

import random
from datetime import datetime
from typing import Optional


class Messages:
    """
    A collection of friendly, helpful messages for every situation.
    
    We keep all our copy in one place so the tone stays consistent
    and we can easily tweak things without hunting through code.
    """
    
    # ─────────────────────────────────────────────────────────────
    # Welcome & Onboarding
    # ─────────────────────────────────────────────────────────────
    
    WELCOME_FIRST_RUN = """
    👋 Welcome to Automation Mail!
    
    Let's get you set up in about 2 minutes.
    
    What you'll need:
      • Your email address
      • An app password (we'll help you create one)
      • A cup of coffee ☕ (optional but recommended)
    
    Ready? Run: automation-mail configure
    """
    
    WELCOME_BACK = """
    📧 Welcome back! What would you like to send today?
    
    Quick commands:
      send     → Single email
      bulk     → Multiple recipients
      schedule → Send later
    """
    
    # ─────────────────────────────────────────────────────────────
    # Success Messages — Celebrate the wins!
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def email_sent(recipient: str) -> str:
        """After successfully sending a single email."""
        return f"""
✨ Sent! Your email is on its way to {recipient}.

It should arrive within a minute or two. If it doesn't show up,
check spam folders — sometimes overzealous filters grab legitimate mail.
        """
    
    @staticmethod
    def bulk_complete(sent: int, failed: int, retrying: int) -> str:
        """Summary after completing a bulk send operation."""
        if failed == 0 and retrying == 0:
            return f"""
🎉 Perfect run! All {sent} emails sent successfully.

Your recipients should start seeing them shortly.
"""
        elif failed == 0:
            return f"""
✅ Done! {sent} emails sent, {retrying} still retrying.

Those retrying ones hit temporary issues — they'll go out soon.
"""
        else:
            return f"""
📊 Finished with some hiccups:

  ✓ {sent} sent successfully
  ⚠ {retrying} retrying
  ✗ {failed} couldn't be sent

Check the log file for details on what went wrong.
"""
    
    @staticmethod
    def scheduled(recipient: str, scheduled_time: str) -> str:
        """After scheduling an email for later."""
        return f"""
⏰ Scheduled! Your email to {recipient} will go out at {scheduled_time}.

We'll keep it safe until then. You can check scheduled emails with:
  automation-mail list-scheduled
"""
    
    # ─────────────────────────────────────────────────────────────
    # Error Messages — Helpful, not scary
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def invalid_email(email: str) -> str:
        """When an email address doesn't look right."""
        return f"""
😬 Hmm, "{email}" doesn't look like a valid email address.

Expected format: name@domain.com

Common slip-ups:
  • Missing the @ symbol
  • Typo in the domain (.con instead of .com)
  • Extra spaces hiding at the start or end

💡 Double-check the spelling and try again.
"""
    
    @staticmethod
    def smtp_auth_failed(provider: Optional[str] = None) -> str:
        """When SMTP authentication fails."""
        if provider and provider.lower() == "gmail":
            return """
🔒 Gmail authentication failed.

This usually means you're using your regular password — Gmail
requires a special "App Password" for third-party apps.

How to fix (takes about 2 minutes):
  1. Go to: https://myaccount.google.com/apppasswords
  2. You might need to enable 2FA first
  3. Create a new app password for "Mail"
  4. Copy the 16-character password (ignore spaces)
  5. Use THAT in your .env file, not your regular password

Still stuck? Check: docs/SETUP.md#gmail
"""
        elif provider and provider.lower() in ("outlook", "hotmail", "microsoft"):
            return """
🔒 Outlook authentication failed.

Quick checklist:
  ✓ Using your full email as the username?
  ✓ Created an app password in security settings?
  ✓ SMTP enabled in your Outlook settings?

Microsoft's security can be picky — the app password approach
usually works best.

Guide: docs/SETUP.md#outlook
"""
        else:
            return """
🔒 SMTP authentication failed.

Double-check your .env file:
  • SMTP_USERNAME — usually your full email address
  • SMTP_PASSWORD — might need to be an app-specific password

Many email providers now require app passwords instead of your
regular login password for security reasons.

Need help? Run: automation-mail troubleshoot
"""
    
    @staticmethod
    def connection_failed(host: str, port: int) -> str:
        """When we can't connect to the SMTP server."""
        return f"""
🌐 Couldn't connect to {host}:{port}

Possible causes:
  • Firewall blocking the connection
  • Wrong port number (common ones: 587, 465, 25)
  • SMTP server is down (rare, but it happens)
  • Typo in the hostname

Things to try:
  1. Check if you can reach {host} from your network
  2. Verify the port matches your provider's docs
  3. Try port 465 if 587 isn't working (or vice versa)

💡 Tip: Corporate networks sometimes block SMTP ports.
"""
    
    @staticmethod
    def template_not_found(path: str) -> str:
        """When a template file doesn't exist."""
        return f"""
📄 Couldn't find the template at: {path}

Make sure:
  • The file path is correct (check for typos)
  • The file actually exists
  • You have permission to read it

Available templates in templates/:
  • modern_newsletter.html
  • elegant_invitation.html
  • clean_notification.txt
"""
    
    @staticmethod
    def csv_not_found(path: str) -> str:
        """When a CSV file doesn't exist."""
        return f"""
📋 Couldn't find the recipients file at: {path}

Expected a CSV file with at least an 'email' column.

Example format:
  email,first_name,company
  maya@studio.io,Maya,Design Studio
  james@techforge.co,James,TechForge
"""
    
    @staticmethod
    def rate_limit_hit(limit: int, period: str) -> str:
        """When hitting the provider's rate limit."""
        return f"""
⏸️  Whoa there! You've hit the sending limit.

Your provider allows {limit} emails per {period}.

What you can do:
  • Wait for the limit to reset (usually an hour)
  • Spread the campaign over multiple days
  • Use smaller batches

Pro tip: We automatically space out emails to avoid this,
but huge batches can still trigger limits.
"""
    
    # ─────────────────────────────────────────────────────────────
    # Progress & Status
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def preparing_email() -> str:
        return "📧 Preparing your email..."
    
    @staticmethod
    def sending_bulk(count: int) -> str:
        return f"📬 Sending to {count} recipients..."
    
    @staticmethod
    def testing_connection() -> str:
        return "🔌 Testing connection to your email provider..."
    
    @staticmethod
    def loading_template(name: str) -> str:
        return f"📄 Loading template: {name}"
    
    @staticmethod
    def reading_recipients(path: str) -> str:
        return f"📋 Reading recipients from: {path}"
    
    # ─────────────────────────────────────────────────────────────
    # Tips & Guidance
    # ─────────────────────────────────────────────────────────────
    
    TIPS = [
        "💡 Test with your own email first before sending to clients.",
        "💡 Gmail allows ~500 emails/day. Start small to test deliverability.",
        "💡 Check spam folders if emails don't arrive — first sends often land there.",
        "💡 Personalized subject lines get higher open rates.",
        "💡 Use {{first_name}} in templates for that personal touch.",
    ]
    
    @staticmethod
    def random_tip() -> str:
        return random.choice(Messages.TIPS)
    
    # ─────────────────────────────────────────────────────────────
    # Milestones — Celebrate progress!
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def check_milestone(emails_sent: int) -> Optional[str]:
        """Return a celebration message for milestones, or None."""
        milestones = {
            10: "🎯 10 emails sent! You're getting the hang of this.",
            50: "📈 50 emails! That's a solid start.",
            100: "🎉 100 emails sent with Automation Mail! Nice work!",
            500: "🌟 500 emails! You're a power user now.",
            1000: "🏆 1,000 emails! You've truly mastered this.",
            5000: "🚀 5,000 emails! That's some serious automation.",
            10000: "💎 10,000 emails! Legendary status achieved!",
        }
        return milestones.get(emails_sent)
    
    # ─────────────────────────────────────────────────────────────
    # Smart Greetings
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def smart_greeting(name: str) -> str:
        """
        Returns a context-aware greeting based on time of day and week.
        
        Because "Dear Sir/Madam" belongs in the 90s.
        """
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        # Holiday season (December 20-31)
        if now.month == 12 and now.day >= 20:
            return f"Happy holidays, {name}! 🎄"
        
        # Friday vibes
        if weekday == 4:
            return f"Happy Friday, {name}! 🎉"
        
        # Monday motivation
        if weekday == 0:
            return f"Happy Monday, {name}! ☕"
        
        # Time-based greetings
        if hour < 12:
            return f"Good morning, {name}!"
        elif hour < 17:
            return f"Good afternoon, {name}!"
        else:
            return f"Good evening, {name}!"
