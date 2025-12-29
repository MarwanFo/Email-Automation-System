<div align="center">

# 📧 Automation Mail

**Send smarter, not harder**

A thoughtfully designed email automation tool that doesn't feel like it was made by a robot.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-2c3e50.svg?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-f39c12.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️-e74c3c.svg?style=flat-square)](https://github.com/yourusername/automation-mail)

[Features](#-features) • [Quick Start](#-quick-start) • [Examples](#-examples) • [Templates](#-templates) • [Docs](#-documentation)

</div>

---

## 🌟 Why Automation Mail?

Because sending emails shouldn't feel like programming a spaceship.

We built this after getting frustrated with tools that either:
- Required a PhD to configure
- Had error messages written by robots, for robots
- Looked like they were designed in 2005

**Automation Mail is different:**

- **Human-friendly** — Error messages that actually help you fix things
- **Beautiful CLI** — Progress bars, colors, and a bit of personality
- **Just works** — 5 minutes from install to sending your first email
- **Thoughtful design** — Built by humans, for humans

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📬 **Send & Bulk** | Single emails or thousands from a CSV |
| 🎨 **Templates** | Beautiful HTML templates with `{{variables}}` |
| ⏰ **Scheduling** | Queue emails for the perfect moment |
| 🔄 **Auto-retry** | Temporary failures? We handle it |
| 📊 **Smart Logging** | Know exactly what happened |
| 🔒 **Secure** | Credentials never logged |
| 💅 **Beautiful CLI** | Progress bars and friendly messages |

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/automation-mail.git
cd automation-mail

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the CLI
pip install -e .
```

### Configuration (2 minutes)

Run the interactive setup wizard:

```bash
automation-mail configure
```

Or copy the example config:

```bash
cp .env.example .env
# Edit .env with your email settings
```

### Send Your First Email

```bash
automation-mail send \
  --to friend@example.com \
  --subject "Hello from Automation Mail!" \
  --body "This is way easier than I expected."
```

That's it! ✨

---

## 📸 Examples

### Single Email

```bash
automation-mail send \
  --to sarah@designstudio.io \
  --subject "Quick question about the project" \
  --body "Hey Sarah, do you have 5 minutes to chat today?"
```

### Bulk Email Campaign

```bash
# Send newsletter to everyone in your CSV
automation-mail bulk \
  --recipients clients.csv \
  --template templates/modern_newsletter.html \
  --subject "Our December Update"
```

Your CSV should look like:
```csv
email,first_name,company
maya@studio.io,Maya,Design Studio
james@techforge.co,James,TechForge
```

### Schedule for Later

```bash
automation-mail schedule \
  --to team@company.com \
  --subject "Team meeting in 1 hour" \
  --body "Don't forget! Zoom link: ..." \
  --when "tomorrow 9am"
```

### With Attachments

```bash
automation-mail send \
  --to client@company.com \
  --subject "Q4 Report Attached" \
  --body "Please find the report attached." \
  --attach report.pdf \
  --attach supplementary-data.xlsx
```

---

## 🎨 Templates

We include 3 handcrafted email templates:

| Template | Best For |
|----------|----------|
| `modern_newsletter.html` | Newsletters, updates, announcements |
| `elegant_invitation.html` | Events, webinars, special occasions |
| `clean_notification.txt` | Plain text alerts and notifications |

### Using Templates

Templates use `{{variable}}` syntax for personalization:

```html
<h1>Hey {{first_name}}!</h1>
<p>Your subscription to {{company}} expires on {{expiry_date}}.</p>
```

Variables are pulled from your CSV columns during bulk sends.

### Creating Your Own

Drop any `.html` or `.txt` file in the `templates/` directory:

```bash
automation-mail templates  # List all available templates
```

---

## 📋 All Commands

| Command | Description |
|---------|-------------|
| `configure` | Interactive setup wizard |
| `test-connection` | Verify your SMTP settings |
| `send` | Send a single email |
| `bulk` | Send to multiple recipients |
| `schedule` | Schedule for later |
| `list-scheduled` | View scheduled emails |
| `cancel <id>` | Cancel a scheduled email |
| `templates` | List available templates |
| `troubleshoot` | Diagnose common issues |

Get help for any command:
```bash
automation-mail send --help
```

---

## 🛠️ Pro Tips

1. **Test first** — Always send to yourself before a big campaign
2. **Start small** — Try 10 recipients, then scale up
3. **Check spam** — Your first few emails might land in spam folders
4. **Mind the limits** — Gmail: 500/day, Outlook: 300/day
5. **Be patient** — Large campaigns take time (that's a feature, not a bug!)

---

## 📚 Documentation

For detailed guides, check out:

| Guide | Description |
|-------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete feature walkthrough |
| [Setup Guide](docs/SETUP.md) | Gmail, Outlook, and custom SMTP |
| [Examples](docs/EXAMPLES.md) | Real-world use cases |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Fix common issues |

---

## 🏗️ Project Structure

```
automation-mail/
├── src/                    # Main source code
│   ├── main.py            # CLI entry point
│   ├── email_sender.py    # SMTP logic
│   ├── template_engine.py # Jinja2 templates
│   ├── scheduler.py       # Job queue
│   └── ui/                # Beautiful output
├── templates/             # Email templates
├── data/                  # Sample data & databases
├── docs/                  # Documentation
└── tests/                 # Test suite
```

---

## 🤝 Contributing

Found a bug? Have an idea? Contributions welcome!

1. Fork it
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License — use it for anything you like!

---

## 💙 Made with Love

Built by humans who were tired of robotic email tools.

If Automation Mail helps you, consider giving it a ⭐ on GitHub!

---

<div align="center">

**[⬆ back to top](#-automation-mail)**

</div>
