# Troubleshooting Guide

> Solutions to common problems.

---

## Quick Diagnostic

Run this first:

```bash
automation-mail troubleshoot
```

This checks:
- ✓ Configuration file exists
- ✓ All required settings are present
- ✓ SMTP connection works
- ✓ Authentication succeeds

---

## Authentication Errors

### "Gmail authentication failed"

**Symptoms:**
- Error mentions "Username and Password not accepted"
- Works in other apps but not here

**Solution:**
1. You're probably using your regular password — Gmail requires an **App Password**
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. If you don't see this option, enable [2-Step Verification](https://myaccount.google.com/security) first
4. Create an app password and use that in your `.env`

### "Outlook authentication failed"

**Symptoms:**
- Error mentions authentication or login failed

**Solutions:**
1. **Check if SMTP is enabled:**
   - Microsoft 365 Admin > Users > Your user > Mail > Manage email apps
   - Enable "Authenticated SMTP"

2. **Use an app password:**
   - Go to [Account Security](https://account.live.com/proofs/Manage)
   - Create an app password

3. **Check your tenant settings:**
   - Some organizations disable SMTP entirely
   - Contact your IT admin

### "Authentication failed" (generic)

**Checklist:**
- [ ] Username is your full email address (not just "john")
- [ ] Password is the app password, not your regular password
- [ ] No extra spaces before/after the password in `.env`
- [ ] Password doesn't contain special characters that need quoting

---

## Connection Errors

### "Connection refused"

**Symptoms:**
- Error mentions "Connection refused" or "couldn't connect"

**Solutions:**

1. **Check the hostname:**
   - Gmail: `smtp.gmail.com`
   - Outlook: `smtp.office365.com`
   - Yahoo: `smtp.mail.yahoo.com`

2. **Try a different port:**
   ```env
   # Option 1: TLS on port 587 (most common)
   SMTP_PORT=587
   SMTP_USE_TLS=true
   SMTP_USE_SSL=false
   
   # Option 2: SSL on port 465
   SMTP_PORT=465
   SMTP_USE_TLS=false
   SMTP_USE_SSL=true
   
   # Option 3: Alternative port
   SMTP_PORT=2525
   SMTP_USE_TLS=true
   ```

3. **Check if your network blocks SMTP:**
   - Corporate networks often block port 25, 587, 465
   - Try from a different network (home, mobile hotspot)

### "Connection timed out"

**Symptoms:**
- Takes a long time, then fails

**Solutions:**
- Firewall might be blocking the connection
- Try increasing timeout in `.env`:
  ```env
  SMTP_TIMEOUT=60
  ```
- Your ISP might block SMTP — try a different network

---

## Email Sending Issues

### Emails not arriving

**Check these in order:**

1. **Spam folder** — Most common! Check recipient's spam folder

2. **Sending limit** — Did you exceed your provider's limit?
   - Gmail: 500/day
   - Outlook: 300/day

3. **SPF/DKIM** — For custom domains, check DNS records:
   ```bash
   # Check SPF record
   nslookup -type=txt yourdomain.com
   ```

4. **Blacklisted** — Check if your IP is blacklisted:
   - [MXToolbox](https://mxtoolbox.com/blacklists.aspx)

### "Recipient refused"

**Symptoms:**
- Works for some recipients, not others

**Causes:**
- Typo in email address
- Recipient's mailbox is full
- Their server is rejecting you (spam filters)

**Solution:**
- Verify the email address
- Try a different recipient
- Check your sender reputation

### Emails going to spam

**Prevention tips:**
1. Use a proper "From" name and email
2. Include an unsubscribe link
3. Avoid spammy words in subject (FREE!, ACT NOW!)
4. Don't use all caps
5. Keep images reasonable
6. Send from a consistent address

---

## Template Errors

### "Template not found"

**Check:**
- File path is correct
- File exists in `templates/` directory
- Correct file extension (`.html` or `.txt`)

```bash
# List available templates
automation-mail templates
```

### "Template syntax error"

**Common causes:**

1. **Unclosed brackets:**
   ```html
   <!-- Wrong -->
   {{first_name}
   
   <!-- Right -->
   {{first_name}}
   ```

2. **Missing closing tags:**
   ```html
   <!-- Wrong -->
   {% if something %}
   
   <!-- Right -->
   {% if something %}
   ...
   {% endif %}
   ```

3. **Invalid variable names:**
   ```html
   <!-- Wrong: spaces in variable names -->
   {{first name}}
   
   <!-- Right -->
   {{first_name}}
   ```

### Variables not substituting

**Check:**
- CSV column names match template variables exactly
- Column names are lowercase (case-sensitive)
- No leading/trailing spaces in CSV headers

---

## CSV Errors

### "Missing email column"

Your CSV needs an `email` column:
```csv
email,first_name
maya@example.com,Maya
```

Not:
```csv
Email Address,First Name
maya@example.com,Maya
```

### "Invalid email in row X"

The email in that row has an issue:
- Missing `@` symbol
- Typo in domain (`gmail.con`)
- Extra spaces

### CSV encoding issues

**Symptoms:**
- Weird characters in names
- "Can't read file" errors

**Solution:**
Save CSV as UTF-8:
1. Open in Excel
2. File > Save As
3. Format: CSV UTF-8 (Comma delimited)

---

## Scheduling Issues

### Scheduled emails not sending

For scheduled emails to be sent, you need to run the scheduler:

```bash
# In a separate terminal (or as a background service)
python -c "from src.scheduler import get_scheduler; s = get_scheduler(); s.run()"
```

Or set up a cron job to check periodically.

### Wrong timezone

Check your `.env`:
```env
SCHEDULER_TIMEZONE=America/New_York
```

Use IANA timezone names, not abbreviations like EST.

---

## Performance Issues

### Sending is very slow

**This is by design!** We space emails to avoid triggering spam filters.

Current rate: ~8 emails/minute (configurable)

To speed up:
```env
RATE_LIMIT_EMAILS_PER_MINUTE=15
```

> ⚠️ Going too fast may get you flagged as spam

### Out of memory on large campaigns

For very large CSVs (10,000+ rows):
- Consider splitting into smaller batches
- Use the `--limit` flag to test first

---

## Configuration Issues

### ".env not found"

Create it from the example:
```bash
cp .env.example .env
```

Then edit with your settings.

### "Missing required configuration"

Check your `.env` file includes these required values:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SENDER_NAME`
- `SENDER_EMAIL`

---

## Still Stuck?

1. **Check the logs:**
   ```bash
   cat logs/automation-mail.log
   ```

2. **Run in debug mode:**
   ```env
   LOG_LEVEL=DEBUG
   ```

3. **Test with minimal setup:**
   ```bash
   automation-mail send \
     --to your.own.email@gmail.com \
     --subject "Test" \
     --body "Testing 123"
   ```

4. **Check our issues page** for known problems

---

*Most problems are either authentication (wrong password type) or network (blocked ports). Start there!*
