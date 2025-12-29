# User Guide

> Everything you need to know about Automation Mail.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Sending Emails](#sending-emails)
3. [Bulk Campaigns](#bulk-campaigns)
4. [Templates](#templates)
5. [Scheduling](#scheduling)
6. [Best Practices](#best-practices)

---

## Getting Started

### First-Time Setup

After installing Automation Mail, run the configuration wizard:

```bash
automation-mail configure
```

This interactive wizard will:
1. Ask which email provider you use (Gmail, Outlook, or custom)
2. Collect your email credentials
3. Create a `.env` file with your settings
4. Optionally test the connection

### Verifying Your Setup

Always test before sending real emails:

```bash
automation-mail test-connection
```

You should see:
```
🔌 Testing connection to your email provider...
✓ Connection successful! Your SMTP settings look good.
You're ready to send emails! 🚀
```

If something's wrong, run:
```bash
automation-mail troubleshoot
```

---

## Sending Emails

### Basic Email

The simplest way to send an email:

```bash
automation-mail send \
  --to recipient@example.com \
  --subject "Hello!" \
  --body "This is my message."
```

### With HTML Content

For rich formatting, use the `--html` flag:

```bash
automation-mail send \
  --to client@company.com \
  --subject "Proposal" \
  --html "<h1>Hello!</h1><p>Here's our proposal...</p>"
```

### Using Templates

For complex emails, use a template file:

```bash
automation-mail send \
  --to client@company.com \
  --subject "Monthly Update" \
  --template templates/modern_newsletter.html
```

### Adding Attachments

Attach one or more files:

```bash
automation-mail send \
  --to boss@work.com \
  --subject "Q4 Report" \
  --body "Please find the reports attached." \
  --attach report.pdf \
  --attach summary.xlsx
```

### CC and BCC

Copy others on your email:

```bash
automation-mail send \
  --to client@company.com \
  --subject "Project Update" \
  --body "Here's where we stand..." \
  --cc manager@work.com \
  --bcc archive@work.com
```

### Dry Run Mode

Preview without actually sending:

```bash
automation-mail send \
  --to test@example.com \
  --subject "Test" \
  --body "Testing..." \
  --dry-run
```

---

## Bulk Campaigns

### Preparing Your Recipient List

Create a CSV file with at least an `email` column:

```csv
email,first_name,last_name,company
maya@studio.io,Maya,Patel,Design Studio
james@tech.co,James,Morrison,TechForge
lisa@artisan.co,Lisa,Rodriguez,Artisan Co
```

> 💡 Column names become template variables. Use `{{first_name}}` in your template.

### Sending a Bulk Campaign

```bash
automation-mail bulk \
  --recipients clients.csv \
  --template templates/modern_newsletter.html \
  --subject "Our December Newsletter"
```

### Personalized Subjects

Use template variables in your subject line too:

```bash
automation-mail bulk \
  --recipients leads.csv \
  --template welcome.html \
  --subject "Welcome to the team, {{first_name}}!"
```

### Preview Mode

Check everything before sending:

```bash
automation-mail bulk \
  --recipients clients.csv \
  --template newsletter.html \
  --subject "Update" \
  --preview
```

### Limiting Recipients (Testing)

Send to only the first N recipients:

```bash
automation-mail bulk \
  --recipients clients.csv \
  --template newsletter.html \
  --subject "Test" \
  --limit 5
```

### What to Expect

During a bulk send, you'll see:
- A preview of your recipients
- A progress bar showing emails sent
- Real-time success/failure counts
- A summary when complete
- Location of the detailed log file

---

## Templates

### Available Templates

List all templates:

```bash
automation-mail templates
```

We include 3 built-in templates:

| Template | Type | Best For |
|----------|------|----------|
| `modern_newsletter.html` | HTML | Newsletters, updates |
| `elegant_invitation.html` | HTML | Events, invitations |
| `clean_notification.txt` | Text | Alerts, reminders |

### Template Variables

Templates use Jinja2 syntax for variables:

```html
<p>Hey {{first_name}},</p>
<p>Thanks for joining {{company}}!</p>
```

### Available Filters

Transform data with built-in filters:

| Filter | Example | Result |
|--------|---------|--------|
| `title` | `{{name\|title}}` | "john doe" → "John Doe" |
| `first_name` | `{{full_name\|first_name}}` | "John Doe" → "John" |
| `currency` | `{{amount\|currency}}` | 1234.5 → "$1,234.50" |
| `date` | `{{date\|date}}` | ISO date → "January 15, 2025" |

### Creating Custom Templates

1. Create a new file in `templates/`:
   ```bash
   # Example: templates/my_template.html
   ```

2. Add your HTML with variables:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>{{subject}}</title>
   </head>
   <body>
       <h1>Hello {{first_name}}!</h1>
       <p>{{message}}</p>
   </body>
   </html>
   ```

3. Use it:
   ```bash
   automation-mail send \
     --to friend@email.com \
     --subject "Hi!" \
     --template templates/my_template.html
   ```

---

## Scheduling

### Schedule an Email

Send an email at a specific time:

```bash
automation-mail schedule \
  --to team@company.com \
  --subject "Monday Standup Reminder" \
  --body "Don't forget: standup at 9am!" \
  --when "tomorrow 8:30am"
```

### Supported Time Formats

| Format | Example |
|--------|---------|
| Relative | `in 2 hours`, `in 30 minutes` |
| Tomorrow | `tomorrow 9am`, `tomorrow 2:30pm` |
| Date + Time | `2025-01-15 14:00` |
| ISO Format | `2025-01-15T14:00:00` |

### View Scheduled Emails

```bash
automation-mail list-scheduled
```

Show all jobs (including sent/failed):
```bash
automation-mail list-scheduled --all
```

### Cancel a Scheduled Email

```bash
automation-mail cancel 42  # Replace 42 with the job ID
```

### How Scheduling Works

Scheduled emails are stored in a local SQLite database. They persist across restarts and are processed when their scheduled time arrives.

> ⚠️ Note: For scheduled emails to be sent, you need to have a process running that checks for due emails. This can be automated with a cron job or system service.

---

## Best Practices

### Before Your First Campaign

1. **Test with yourself** — Send to your own email first
2. **Check spam folders** — First sends often land in spam
3. **Start small** — Try 10 recipients before sending to 1000
4. **Use clear subjects** — Avoid "test" or "hello"

### Rate Limiting

Email providers have sending limits:

| Provider | Limit |
|----------|-------|
| Gmail | ~500/day |
| Outlook | ~300/day |
| Most ISPs | ~100-200/day |

Automation Mail automatically spaces out emails to avoid triggering limits.

### Deliverability Tips

1. **Personalize** — Use `{{first_name}}` for better engagement
2. **Clear subjects** — Be specific about the content
3. **Easy unsubscribe** — Include an unsubscribe link
4. **Consistent sender** — Use the same from address
5. **Test first** — Always send a test email

### Avoiding Spam Filters

- Don't use ALL CAPS in subjects
- Avoid excessive punctuation (!!!)
- Don't use "FREE" or "URGENT" too much
- Include a physical address (required by law in many countries)
- Provide an unsubscribe option

---

## Getting Help

### Troubleshooting

Run the diagnostic tool:
```bash
automation-mail troubleshoot
```

### Command Help

Get help for any command:
```bash
automation-mail --help
automation-mail send --help
automation-mail bulk --help
```

### Documentation

- [Setup Guide](SETUP.md) — Provider-specific configuration
- [Examples](EXAMPLES.md) — Real-world use cases
- [Troubleshooting](TROUBLESHOOTING.md) — Fixing common issues

---

*Happy emailing! ✉️*
