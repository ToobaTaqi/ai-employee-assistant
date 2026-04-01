# AI Employee System - Silver + Gold Tier Complete

> **Your Personal AI Employee - Local-First, Agent-Driven, Human-in-the-Loop**

A complete AI-powered employee system that proactively manages your business communications and tasks 24/7 using Qwen Code, Obsidian, and automated watchers.

---

## 🏆 Hackathon Status

**Tier:** Silver + Gold Tier Complete  
**Status:** ✅ Production Ready  
**Testing:** 10/12 components tested and working  

---

## ✨ Key Features

### Perception Layer (Watchers)
- **📧 Gmail Watcher** - Monitors Gmail for unread/important emails
- **💬 WhatsApp Watcher** - Monitors WhatsApp Web for priority messages
- **📁 File System Watcher** - Watches drop folder for new files

### Reasoning Layer
- **🧠 Plan Generator** - Creates structured task plans automatically
- **🔄 Task Scheduler** - Cron-like scheduling for automated tasks
- **🔁 Ralph Wiggum Loop** - Keeps Qwen working until tasks complete

### Action Layer
- **📧 Email MCP Server** - Send emails via Gmail API with HITL approval
- **📱 LinkedIn Auto-Poster** - Create drafts and auto-post to LinkedIn
- **💼 Odoo MCP Server** - Accounting integration (invoices, payments)

### Workflow & Reliability
- **✅ Approval Orchestrator** - Human-in-the-Loop approval workflow
- **📊 Dashboard Updater** - Real-time status dashboard
- **📈 Briefing Generator** - Daily/weekly CEO briefings
- **🛡️ Error Recovery System** - Comprehensive error handling & audit logging

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd AI_Employee_Vault/scripts
pip install -r requirements.txt
playwright install chromium
```

### 2. Verify Installation

```bash
python verify_silver_gold.py
```

### 3. Start the System

```bash
# Start task scheduler (runs all automated tasks)
python task_scheduler.py --daemon

# Or start individual watchers
python gmail_watcher.py
python whatsapp_watcher.py --visible
python filesystem_watcher.py
```

---

## 📁 Folder Structure

```
AI_Employee_Vault/
├── 📄 Dashboard.md              # Real-time status dashboard
├── 📄 Company_Handbook.md       # Business rules & guidelines
├── 📄 README.md                 # This file
├── 📁 Inbox/                    # Drop zone for new files
├── 📁 Needs_Action/             # Tasks awaiting processing
├── 📁 Done/                     # Completed tasks
├── 📁 Pending_Approval/         # Awaiting human decision
├── 📁 Approved/                 # Approved actions
├── 📁 Rejected/                 # Rejected actions
├── 📁 Briefings/                # Generated reports
├── 📁 Plans/                    # Task plans
├── 📁 Accounting/               # Financial records
├── 📁 Social_Media/LinkedIn/    # LinkedIn posts
├── 📁 Processing/               # Files being processed
├── 📁 logs/                     # System logs
└── 📁 scripts/                  # All Python scripts
    ├── gmail_watcher.py
    ├── whatsapp_watcher.py
    ├── email_mcp_server.py
    ├── task_scheduler.py
    └── ... (10 more scripts)
```

---

## 🧪 Testing Guide

Complete testing guides are in `testing_guide/` folder:

| # | Component | Status | Guide |
|---|-----------|--------|-------|
| 1 | Plan Generator | ✅ Pass | `testing_guide/01_plan_generator.md` |
| 2 | Dashboard Updater | ✅ Pass | `testing_guide/02_dashboard_updater.md` |
| 3 | Briefing Generator | ✅ Pass | `testing_guide/03_briefing_generator.md` |
| 4 | Task Scheduler | ✅ Pass | `testing_guide/04_task_scheduler.md` |
| 5 | Approval Orchestrator | ✅ Pass | `testing_guide/05_approval_orchestrator.md` |
| 6 | Email MCP Server | ✅ Pass | `testing_guide/06_email_mcp_server.md` |
| 7 | Gmail Watcher | ✅ Pass | `testing_guide/07_gmail_watcher.md` |
| 8 | WhatsApp Watcher | ⚠️ Partial | `testing_guide/08_whatsapp_watcher.md` |
| 9 | LinkedIn Auto-Poster | ✅ Pass | `testing_guide/09_linkedin_poster.md` |
| 10 | Ralph Wiggum Loop | ✅ Pass | `testing_guide/10_ralph_wiggum.md` |
| 11 | Error Recovery | ✅ Pass | `testing_guide/11_error_recovery.md` |
| 12 | Odoo MCP Server | ⬜ Skip | `testing_guide/12_odoo_mcp.md` |

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | This file - overview and quick start |
| `SILVER_GOLD_SETUP.md` | Complete setup guide |
| `IMPLEMENTATION_SUMMARY.md` | What was built |
| `WHATSAPP_WATCHER_GUIDE.md` | WhatsApp setup & troubleshooting |
| `testing_guide/README.md` | Testing roadmap |
| `testing_guide/COMPLETION_CHECKLIST.md` | Track test progress |

---

## 🔧 Configuration

### Gmail Setup

1. Enable Gmail API in Google Cloud Console
2. Create OAuth2 credentials
3. Save as `credentials/credentials.json`
4. Run: `python gmail_watcher.py --auth`

### WhatsApp Setup

```bash
python whatsapp_watcher.py --visible
# Scan QR code when browser opens
```

### LinkedIn Setup

Just create drafts - posting is manual or via approval workflow:

```bash
python linkedin_poster.py --draft "Your post content"
python linkedin_poster.py --post-auto  # Auto-post latest draft
```

---

## 🎯 Usage Examples

### Monitor Gmail Continuously

```bash
python gmail_watcher.py --interval 120
```

### Create LinkedIn Post Draft

```bash
python linkedin_poster.py --draft "Excited to announce our new AI system! #AI #Automation"
```

### Generate Daily Briefing

```bash
python briefing_generator.py --type daily
```

### Process All Pending Tasks

```bash
python task_scheduler.py --run-once
```

---

## 🛡️ Security Notes

- **Local-First**: All data stored locally in Obsidian vault
- **Credentials**: Never commit `credentials/` folder
- **HITL**: Sensitive actions require human approval
- **Audit Logs**: All actions logged for accountability

---

## 📊 Hackathon Deliverables

### Silver Tier ✅
- [x] Multiple Watchers (Gmail, WhatsApp, File)
- [x] Email MCP Server
- [x] HITL Approval Workflow
- [x] Plan Generation
- [x] Task Scheduler
- [x] Dashboard Updates
- [x] Briefing Generation

### Gold Tier ✅
- [x] Ralph Wiggum Persistence Loop
- [x] Odoo MCP Server (code complete)
- [x] LinkedIn Auto-Posting
- [x] CEO Briefing System
- [x] Error Recovery & Audit Logging

---

## 🐛 Known Issues

| Component | Issue | Workaround |
|-----------|-------|------------|
| WhatsApp Watcher | Browser restart fails on Windows | Use longer intervals (60s+) or PM2 |
| Ralph Wiggum | Requires Qwen Code approval | Manual file movement or interactive approval |

---

## 🤝 Contributing

This is a hackathon project. Feel free to:
1. Fork and improve
2. Report issues
3. Suggest features

---

## 📄 License

MIT License - See LICENSE file

---

## 🎓 Credits

Built for **Panaversity Hackathon 0: Building Autonomous FTEs in 2026**

**Architecture:** Based on "Personal AI Employee Hackathon 0" blueprint  
**Tech Stack:** Qwen Code, Obsidian, Playwright, MCP Servers  

---

*Last Updated: April 1, 2026*  
*AI Employee System v1.0 - Silver + Gold Tier Complete*
