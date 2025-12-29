# Real-World Examples

> Practical examples for common email automation scenarios.

---

## Newsletter Campaign

### Scenario
You run a design studio and want to send a monthly newsletter to 500 clients.

### Setup

1. **Prepare your recipient list** (`clients.csv`):
```csv
email,first_name,company,role
sarah.chen@designstudio.io,Sarah,Chen Design,Creative Director
marcus.johnson@techforge.com,Marcus,TechForge,CTO
lisa.patel@artisangoods.co,Lisa,Artisan Goods,Founder
```

2. **Customize your template** based on `templates/modern_newsletter.html`

3. **Test with yourself first**:
```bash
automation-mail send \
  --to your.email@gmail.com \
  --subject "December Newsletter Preview" \
  --template templates/modern_newsletter.html
```

4. **Send to everyone**:
```bash
automation-mail bulk \
  --recipients clients.csv \
  --template templates/modern_newsletter.html \
  --subject "Chen Design — December Update"
```

---

## Event Invitation

### Scenario
You're hosting a product launch event and need to invite 200 people.

### Setup

1. **Prepare your guest list** (`guests.csv`):
```csv
email,first_name,company,ticket_type
maya.patel@investor.vc,Maya,Riverside Ventures,VIP
james.morrison@press.com,James,Tech Daily,Press
david.kim@client.com,David,Greenleaf Corp,General
```

2. **Customize `templates/elegant_invitation.html`** with your event details

3. **Preview before sending**:
```bash
automation-mail bulk \
  --recipients guests.csv \
  --template templates/elegant_invitation.html \
  --subject "You're Invited: Product Launch 2025" \
  --preview
```

4. **Send invitations**:
```bash
automation-mail bulk \
  --recipients guests.csv \
  --template templates/elegant_invitation.html \
  --subject "You're Invited: Product Launch 2025"
```

---

## Personalized Outreach

### Scenario
You're reaching out to potential clients with personalized messages.

### Setup

1. **Create a detailed CSV** with custom content:
```csv
email,first_name,company,custom_message,relevant_project
maya@vc.com,Maya,Riverside VC,"I noticed your portfolio includes several design-focused startups",Your investment in CloudDesign
james@tech.co,James,TechForge,"We've done similar work for enterprise companies",Your rebrand last year
```

2. **Create a custom template** (`templates/outreach.html`):
```html
<p>Hi {{first_name}},</p>

<p>{{custom_message}}. {{relevant_project}} caught my attention.</p>

<p>I'd love to share some ideas with you — would you have 15 minutes this week?</p>

<p>Best,<br>Your Name</p>
```

3. **Send with personalized subjects**:
```bash
automation-mail bulk \
  --recipients leads.csv \
  --template templates/outreach.html \
  --subject "Quick question about {{company}}"
```

---

## Scheduled Reminders

### Scenario
You want to send meeting reminders 1 hour before each meeting.

### Setup

```bash
# Monday standup reminder
automation-mail schedule \
  --to team@company.com \
  --subject "Standup in 1 hour" \
  --body "Quick reminder: team standup at 9am in the main conf room." \
  --when "2025-01-06 08:00"

# Client call reminder
automation-mail schedule \
  --to your.email@company.com \
  --subject "Client call in 1 hour" \
  --body "Prep reminder: Call with Widget Corp at 2pm. Review proposal before." \
  --when "2025-01-07 13:00"
```

### View scheduled reminders:
```bash
automation-mail list-scheduled
```

---

## Invoice Delivery

### Scenario
Sending monthly invoices to clients with PDF attachments.

### Setup

1. **Prepare your invoice list** (`invoices.csv`):
```csv
email,first_name,company,invoice_number,amount,due_date,pdf_file
maya@client.com,Maya,Widget Corp,INV-2025-001,$2500,January 15 2025,invoices/inv-001.pdf
james@client.com,James,TechForge,INV-2025-002,$4800,January 15 2025,invoices/inv-002.pdf
```

2. **Create an invoice email template** (`templates/invoice.html`):
```html
<p>Hi {{first_name}},</p>

<p>Please find attached invoice {{invoice_number}} for {{amount}}.</p>

<p><strong>Due Date:</strong> {{due_date}}</p>

<p>Payment details are on the invoice. Let me know if you have any questions!</p>

<p>Thanks,<br>Your Company</p>
```

3. **For now, send individually** (bulk doesn't support per-row attachments):
```bash
automation-mail send \
  --to maya@client.com \
  --subject "Invoice INV-2025-001 from Your Company" \
  --template templates/invoice.html \
  --attach invoices/inv-001.pdf
```

---

## Welcome Email Sequence

### Scenario
New users should get a welcome email, then a tips email 3 days later.

### Setup

**Day 1 — Welcome email:**
```bash
automation-mail send \
  --to newuser@example.com \
  --subject "Welcome to Awesome App! 🎉" \
  --template templates/welcome.html
```

**Day 3 — Tips email (scheduled):**
```bash
automation-mail schedule \
  --to newuser@example.com \
  --subject "3 tips to get the most out of Awesome App" \
  --template templates/tips.html \
  --when "in 3 days"
```

---

## Internal Team Updates

### Scenario
Weekly project status update to your team.

### Setup

1. **Create a simple template** (`templates/team_update.txt`):
```
Weekly Update — {{week_of}}
==================================

Hi team,

Here's where we stand:

COMPLETED THIS WEEK:
{{completed}}

IN PROGRESS:
{{in_progress}}

BLOCKERS:
{{blockers}}

Let me know if you have questions!

— {{sender_name}}
```

2. **Send the update:**
```bash
automation-mail send \
  --to team@company.com \
  --cc manager@company.com \
  --subject "Weekly Update — Week of Jan 6" \
  --template templates/team_update.txt
```

---

## A/B Testing Subject Lines

### Scenario
Test which subject line performs better.

### Setup

1. **Split your recipient list:**
   - `recipients_a.csv` — first half
   - `recipients_b.csv` — second half

2. **Send variant A:**
```bash
automation-mail bulk \
  --recipients recipients_a.csv \
  --template newsletter.html \
  --subject "Your December Update is Here"
```

3. **Send variant B:**
```bash
automation-mail bulk \
  --recipients recipients_b.csv \
  --template newsletter.html \
  --subject "5 things you missed this month"
```

4. **Compare open rates** using your email tracking tool.

---

## Emergency Broadcast

### Scenario
Something's wrong and you need to notify all customers immediately.

### Setup

```bash
# Skip the preview, send immediately
automation-mail bulk \
  --recipients all_customers.csv \
  --template templates/clean_notification.txt \
  --subject "Service Update: Scheduled Maintenance Tonight"
```

> ⚠️ For true emergencies, consider using a transactional email service like SendGrid for higher throughput.

---

## Multi-Language Campaigns

### Scenario
Send newsletters in different languages based on user preference.

### Setup

1. **Segment your lists:**
   - `customers_en.csv`
   - `customers_es.csv`
   - `customers_fr.csv`

2. **Create localized templates:**
   - `templates/newsletter_en.html`
   - `templates/newsletter_es.html`
   - `templates/newsletter_fr.html`

3. **Send each:**
```bash
automation-mail bulk --recipients customers_en.csv --template templates/newsletter_en.html --subject "December Newsletter"
automation-mail bulk --recipients customers_es.csv --template templates/newsletter_es.html --subject "Boletín de Diciembre"
automation-mail bulk --recipients customers_fr.csv --template templates/newsletter_fr.html --subject "Newsletter de Décembre"
```

---

*Have a use case we missed? Let us know!*
