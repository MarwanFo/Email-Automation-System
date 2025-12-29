# Setup Guide

> Get Automation Mail connected to your email provider.

---

## Quick Start

The easiest way to set up is the interactive wizard:

```bash
automation-mail configure
```

For manual setup, read on.

---

## Gmail Setup

Gmail is our most popular provider. Here's how to set it up properly.

### Step 1: Enable 2-Factor Authentication

Gmail requires 2FA before you can create app passwords.

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", click **2-Step Verification**
3. Follow the prompts to enable it

### Step 2: Create an App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select app: **Mail**
3. Select device: **Other** (type "Automation Mail")
4. Click **Generate**
5. Copy the 16-character password (ignore spaces)

> ⚠️ Save this password somewhere safe — you won't see it again!

### Step 3: Configure .env

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx    # Your 16-character app password
SMTP_USE_TLS=true

SENDER_NAME=Your Name
SENDER_EMAIL=your.email@gmail.com
```

### Step 4: Test It

```bash
automation-mail test-connection
```

### Gmail Sending Limits

- **Free accounts**: ~500 emails/day
- **Google Workspace**: ~2,000 emails/day

Automation Mail automatically spaces emails to stay under limits.

---

## Outlook / Microsoft 365 Setup

### Step 1: Enable SMTP AUTH

Microsoft disables SMTP by default. Enable it:

1. Sign in to [Microsoft 365 admin center](https://admin.microsoft.com)
2. Go to **Users** > **Active users**
3. Select your user > **Mail** > **Manage email apps**
4. Check **Authenticated SMTP**
5. Save changes

For personal Outlook.com accounts:
1. Go to [Account Security](https://account.live.com/proofs/Manage)
2. Create an app password

### Step 2: Configure .env

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your.email@outlook.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

SENDER_NAME=Your Name
SENDER_EMAIL=your.email@outlook.com
```

### Outlook Sending Limits

- **Outlook.com**: ~300 emails/day
- **Microsoft 365 Business**: ~10,000 emails/day

---

## Yahoo Mail Setup

### Step 1: Generate App Password

1. Sign in to your Yahoo account
2. Go to [Account Security](https://login.yahoo.com/account/security)
3. Scroll to **App Passwords**
4. Click **Generate app password**
5. Select **Other App** and name it "Automation Mail"
6. Copy the password

### Step 2: Configure .env

```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your.email@yahoo.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

SENDER_NAME=Your Name
SENDER_EMAIL=your.email@yahoo.com
```

---

## Zoho Mail Setup

### Step 1: Enable SMTP Access

1. Log in to [Zoho Mail](https://mail.zoho.com)
2. Go to **Settings** > **Mail Accounts**
3. Select your account
4. Under **IMAP & POP**, enable **SMTP Access**

### Step 2: Generate App Password (if using 2FA)

1. Go to [Zoho Account Security](https://accounts.zoho.com/home#security/security)
2. Under **App Passwords**, click **Generate**
3. Name it "Automation Mail"
4. Copy the password

### Step 3: Configure .env

```env
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USERNAME=your.email@zoho.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

SENDER_NAME=Your Name
SENDER_EMAIL=your.email@zoho.com
```

---

## Custom SMTP Setup

For other email providers or self-hosted servers.

### Required Information

Ask your email administrator for:
- SMTP host (e.g., `mail.yourdomain.com`)
- SMTP port (usually 587 for TLS, 465 for SSL)
- Your email/username
- Password or app password
- Whether to use TLS or SSL

### Configuration

```env
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=you@yourdomain.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

SENDER_NAME=Your Name
SENDER_EMAIL=you@yourdomain.com
```

### Port Guide

| Port | Encryption | Typical Use |
|------|------------|-------------|
| 25 | None | Legacy, often blocked |
| 465 | SSL | Implicit SSL (older) |
| 587 | TLS | Most common, recommended |
| 2525 | TLS | Alternative when 587 blocked |

If port 587 doesn't work, try 465 with `SMTP_USE_SSL=true`.

---

## Transactional Email Services

For high-volume sending, consider a dedicated email service.

### SendGrid

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true

SENDER_NAME=Your Name
SENDER_EMAIL=verified@yourdomain.com
```

### Mailgun

```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your-mailgun-smtp-username
SMTP_PASSWORD=your-mailgun-smtp-password
SMTP_USE_TLS=true

SENDER_NAME=Your Name
SENDER_EMAIL=you@your-mailgun-domain.com
```

### Amazon SES

```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
SMTP_USE_TLS=true

SENDER_NAME=Your Name
SENDER_EMAIL=verified-email@yourdomain.com
```

---

## Troubleshooting Setup

### "Authentication Failed"

Most common causes:
1. Using your regular password instead of an app password
2. Typo in the password
3. 2FA not enabled (required for app passwords)

### "Connection Refused"

1. Check hostname spelling
2. Try a different port (587 or 465)
3. Your network might block SMTP ports

### "Certificate Error"

Try these settings:
```env
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Or:
```env
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

### Still Not Working?

Run the diagnostic:
```bash
automation-mail troubleshoot
```

This will check your configuration and connection step by step.

---

## Security Notes

### Keep .env Safe

- Never commit `.env` to git (it's in `.gitignore`)
- Use different passwords for production vs development
- Rotate app passwords periodically

### App Passwords vs Regular Passwords

App passwords are:
- Separate from your main password
- Revokable without changing your main password
- Required when 2FA is enabled
- More secure for third-party apps

---

*Need more help? Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)*
