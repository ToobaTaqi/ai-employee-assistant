# AI Employee - Quick Reference Card

## 🚀 60-Second Setup

```bash
cd AI_Employee_Vault/scripts
pip install -r requirements.txt
playwright install chromium
python verify_silver_gold.py
python task_scheduler.py --daemon
```

---

## 📋 Do I Need Accounts?

| Purpose | Accounts | Command |
|---------|----------|---------|
| **Test basic system** | ❌ None | `python task_scheduler.py --daemon` |
| **Email automation** | ✅ Gmail | `python gmail_watcher.py --auth` |
| **WhatsApp monitoring** | ✅ WhatsApp | `python whatsapp_watcher.py --visible` |
| **LinkedIn posting** | ✅ LinkedIn | `python linkedin_poster.py --login` |
| **Accounting (Odoo)** | ✅ Odoo | `python odoo_mcp_server.py --configure` |

---

## 🧪 Quick Tests (No Accounts)

```bash
# Test 1: File watcher
echo "test" > AI_Employee_Vault/Inbox/test.txt
# Check: AI_Employee_Vault/Needs_Action/

# Test 2: Plan generator
python plan_generator.py
# Check: AI_Employee_Vault/Plans/

# Test 3: Briefing
python briefing_generator.py --type daily
# Check: AI_Employee_Vault/Briefings/

# Test 4: Health check
python error_recovery.py --status
```

---

## 🎯 Start Components

```bash
# Core scheduler (runs all scheduled tasks)
python task_scheduler.py --daemon

# Gmail watcher
python gmail_watcher.py

# WhatsApp watcher
python whatsapp_watcher.py

# Approval processor
python approval_orchestrator.py
```

---

## 📁 Important Folders

| Folder | Purpose |
|--------|---------|
| `Inbox/` | Drop files here for processing |
| `Needs_Action/` | Tasks waiting to be processed |
| `Pending_Approval/` | Awaiting your decision |
| `Approved/` | Move here to approve actions |
| `Rejected/` | Move here to reject actions |
| `Done/` | Completed tasks |
| `Briefings/` | Daily/weekly reports |

---

## 🔍 Check Status

```bash
# System health
python error_recovery.py --status

# Task schedule
python task_scheduler.py --status

# Audit stats
python error_recovery.py --stats

# Dashboard
cat AI_Employee_Vault/Dashboard.md
```

---

## ⚠️ Common Issues

| Problem | Solution |
|---------|----------|
| Module not found | `pip install -r requirements.txt` |
| Gmail auth fails | `rm credentials/gmail_token.json && python gmail_watcher.py --auth` |
| WhatsApp QR missing | `python whatsapp_watcher.py --fresh-session --visible` |
| Playwright error | `playwright install chromium` |

---

## 📖 Full Documentation

- **Setup Guide:** `README_SETUP.md`
- **Silver/Gold Setup:** `SILVER_GOLD_SETUP.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`

---

*Quick Reference - AI Employee System*
