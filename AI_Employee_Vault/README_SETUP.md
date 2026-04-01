# AI Employee System - Complete Setup & Testing Guide

> **Your Personal AI Employee - Local-First, Agent-Driven, Human-in-the-Loop**

This guide walks you through **complete setup, configuration, and testing** of the AI Employee system (Silver + Gold Tier).

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Account Setup (Required for Full Functionality)](#account-setup)
5. [Testing Without Accounts](#testing-without-accounts)
6. [Testing With Accounts](#testing-with-accounts)
7. [Running the Complete System](#running-the-complete-system)
8. [Troubleshooting](#troubleshooting)
9. [What Each Component Does](#what-each-component-does)

---

## 🚀 Quick Start

```bash
# 1. Navigate to scripts folder
cd AI_Employee_Vault/scripts

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Run verification
python verify_silver_gold.py

# 5. Start the system
python task_scheduler.py --daemon
```

**That's it!** The basic system is now running. For full functionality, you'll need to connect accounts (see below).

---

## 📦 Prerequisites

| Software | Version | Download | Required |
|----------|---------|----------|----------|
| **Python** | 3.13+ | [python.org](https://python.org) | ✅ Yes |
| **Node.js** | v24+ LTS | [nodejs.org](https://nodejs.org) | ✅ Yes |
| **Obsidian** | v1.10.6+ | [obsidian.md](https://obsidian.md) | Optional |
| **Qwen Code** | Active | [claude.ai](https://claude.ai) | Optional |
| **Git** | Latest | [git-scm.com](https://git-scm.com) | Optional |

### Check Prerequisites

```bash
# Verify Python
python --version  # Should show 3.13 or higher

# Verify Node.js
node --version  # Should show v24 or higher

# Verify pip
pip --version
```

---

## 🔧 Installation

### Step 1: Install Python Dependencies

```bash
cd AI_Employee_Vault/scripts
pip install -r requirements.txt
```

This installs:
- `watchdog` - File system monitoring
- `google-auth`, `google-api-python-client` - Gmail integration
- `playwright` - Browser automation (WhatsApp, LinkedIn)
- `mcp` - MCP server framework
- `requests` - HTTP client for Odoo
- `pytest` - Testing framework

### Step 2: Install Playwright Browsers

```bash
playwright install chromium
```

This downloads Chromium browser for WhatsApp and LinkedIn automation.

### Step 3: Verify Installation

```bash
python verify_silver_gold.py
```

**Expected Output:**
```
============================================================
  TOTAL: 29/29 checks passed
============================================================
  [SUCCESS] ALL TIERS COMPLETE!
```

---

## 🔐 Account Setup

### Do You Need Accounts?

| Test Type | Accounts Needed | What Works |
|-----------|-----------------|------------|
| **Basic Testing** | ❌ None | File watcher, plan generator, scheduler, briefings |
| **Full Testing** | ✅ Gmail, (optional: WhatsApp, LinkedIn, Odoo) | All features |

### Quick Answer

- **To test the system works:** No accounts needed
- **To use in production:** Gmail required, others optional

---

### 1. Gmail Account (Required for Email Features)

**What it enables:** Email monitoring, sending emails

**Setup Time:** 10 minutes

**Steps:**

1. **Enable Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project (or select existing)
   - Enable "Gmail API"

2. **Create OAuth2 Credentials:**
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: **Desktop app**
   - Download the JSON file

3. **Save Credentials:**
   ```bash
   # Create credentials folder
   mkdir AI_Employee_Vault/credentials
   
   # Save downloaded JSON as:
   # AI_Employee_Vault/credentials/credentials.json
   ```

4. **Authenticate:**
   ```bash
   cd AI_Employee_Vault/scripts
   python gmail_watcher.py --auth
   ```
   - Browser opens
   - Sign in to your Google account
   - Grant permissions
   - Token saved automatically

5. **Test:**
   ```bash
   python gmail_watcher.py --interval 30
   ```
   - Send yourself an email marked "Important"
   - Watch for action file in `Needs_Action/` folder

---

### 2. WhatsApp Account (Optional)

**What it enables:** WhatsApp message monitoring

**Setup Time:** 2 minutes

**⚠️ Warning:** Be aware of WhatsApp's Terms of Service. Use at your own risk.

**Steps:**

1. **First Run (QR Login):**
   ```bash
   python whatsapp_watcher.py --visible
   ```
   - Browser opens to WhatsApp Web
   - Scan QR code with your phone:
     - Open WhatsApp on phone
     - Settings → Linked Devices
     - Link a Device
     - Scan QR code

2. **Subsequent Runs:**
   ```bash
   python whatsapp_watcher.py
   ```
   - Session is saved automatically

3. **Test:**
   - Send yourself a WhatsApp message with keyword "urgent"
   - Watch for action file in `Needs_Action/` folder

---

### 3. LinkedIn Account (Optional)

**What it enables:** Automated LinkedIn posting

**Setup Time:** 2 minutes

**⚠️ Warning:** Be aware of LinkedIn's Terms of Service.

**Steps:**

1. **Login:**
   ```bash
   python linkedin_poster.py --login --email YOUR_EMAIL --password YOUR_PASSWORD
   ```
   - Browser opens
   - Session saved automatically

2. **Test:**
   ```bash
   # Generate content
   python linkedin_poster.py --generate --topic "AI Trends" --tone professional
   
   # Create draft
   python linkedin_poster.py --draft "Test post from AI Employee"
   
   # Check drafts folder
   ls AI_Employee_Vault/Social_Media/LinkedIn/Drafts/
   ```

---

### 4. Odoo Account (Optional - Gold Tier)

**What it enables:** Accounting, invoices, payments

**Setup Time:** 30 minutes (includes Odoo installation)

**Steps:**

1. **Install Odoo Community:**
   - Option A: Local installation from [odoo.com](https://odoo.com)
   - Option B: Docker: `docker run -p 8069:8069 odoo:19.0`

2. **Configure:**
   ```bash
   python odoo_mcp_server.py --configure
   ```
   - Enter Odoo URL (e.g., `http://localhost:8069`)
   - Enter database name
   - Enter username/email
   - Enter password

3. **Test:**
   ```bash
   python odoo_mcp_server.py --test
   ```

---

## 🧪 Testing Without Accounts

You can test **core functionality** without any accounts:

### Test 1: File System Watcher (Bronze)

```bash
# Terminal 1: Start watcher
cd AI_Employee_Vault/scripts
python filesystem_watcher.py
```

```bash
# Terminal 2: Drop a file
echo "Test content" > AI_Employee_Vault/Inbox/test_document.txt
```

**Expected:** Action file created in `Needs_Action/`

---

### Test 2: Plan Generator

```bash
# Create a test action file
cat > AI_Employee_Vault/Needs_Action/TEST_001.md << EOF
---
type: file_drop
original_name: test.txt
status: pending
---

# Test File

Please analyze this test file and create a plan.
EOF

# Generate plan
python plan_generator.py
```

**Expected:** Plan file created in `Plans/` folder

---

### Test 3: Task Scheduler

```bash
# Show scheduled tasks
python task_scheduler.py --status
```

**Expected:** List of 6 scheduled tasks

```bash
# Run due tasks
python task_scheduler.py --run-once
```

**Expected:** Dashboard updated

---

### Test 4: Briefing Generator

```bash
# Generate daily briefing
python briefing_generator.py --type daily

# Generate weekly briefing
python briefing_generator.py --type weekly

# Check output
ls AI_Employee_Vault/Briefings/
```

**Expected:** Briefing files created

---

### Test 5: Error Recovery System

```bash
# Check system health
python error_recovery.py --status

# Show audit statistics
python error_recovery.py --stats
```

**Expected:** Health status and statistics displayed

---

### Test 6: Ralph Wiggum Loop

```bash
# Create state file
python ralph_wiggum.py --prompt "Process all files in Needs_Action"

# Check state
python ralph_wiggum.py --state-file
```

**Expected:** State file created in `Processing/`

---

## 🧪 Testing With Accounts

### Test Gmail Integration

```bash
# 1. Authenticate (first time only)
python gmail_watcher.py --auth

# 2. Start watcher
python gmail_watcher.py --interval 30

# 3. Send test email
# - Send email to yourself from another account
# - Mark as "Important"
# - Subject: "Test - AI Employee"

# 4. Check for action file
ls AI_Employee_Vault/Needs_Action/
```

**Expected:** `EMAIL_*.md` file created within 60 seconds

---

### Test Email Sending (HITL)

```bash
# 1. Create approval request manually
cat > AI_Employee_Vault/Pending_Approval/APPROVAL_Test_Email.md << EOF
---
type: approval_request
action: email_send
to: your-email@gmail.com
subject: Test from AI Employee
body: This is a test email sent by the AI Employee system.
---

Move this file to /Approved to send.
EOF

# 2. Start approval orchestrator
python approval_orchestrator.py --interval 5

# 3. Approve (in another terminal)
mv AI_Employee_Vault/Pending_Approval/APPROVAL_Test_Email.md \
   AI_Employee_Vault/Approved/
```

**Expected:** Email sent, file moved to `Done/`

---

### Test WhatsApp Integration

```bash
# 1. Login (first time)
python whatsapp_watcher.py --visible

# 2. Start watcher
python whatsapp_watcher.py --interval 30

# 3. Send test message
# - Send WhatsApp to yourself with "urgent" keyword

# 4. Check for action file
ls AI_Employee_Vault/Needs_Action/
```

**Expected:** `WHATSAPP_*.md` file created

---

### Test LinkedIn Posting

```bash
# 1. Login
python linkedin_poster.py --login --email EMAIL --password PASSWORD

# 2. Generate content
python linkedin_poster.py --generate --topic "Business Update" --tone professional

# 3. Create draft
python linkedin_poster.py --draft "Testing AI Employee LinkedIn integration!"

# 4. Check drafts
ls AI_Employee_Vault/Social_Media/LinkedIn/Drafts/

# 5. Schedule post
python linkedin_poster.py --schedule --time "2026-03-31 09:00"
```

**Expected:** Draft and scheduled files created

---

### Test Odoo Integration

```bash
# 1. Configure
python odoo_mcp_server.py --configure

# 2. Test connection
python odoo_mcp_server.py --test

# 3. Run as MCP server
python odoo_mcp_server.py
```

**Expected:** Connection successful, financial summary displayed

---

## ▶️ Running the Complete System

### Option 1: Manual (Development)

Open **4 terminals**:

```bash
# Terminal 1: Task Scheduler
cd AI_Employee_Vault/scripts
python task_scheduler.py --daemon

# Terminal 2: Gmail Watcher
python gmail_watcher.py

# Terminal 3: WhatsApp Watcher
python whatsapp_watcher.py

# Terminal 4: Approval Orchestrator
python approval_orchestrator.py
```

---

### Option 2: Windows Task Scheduler (Production)

```batch
:: Run once at startup
schtasks /Create /TN "AI_Employee_Scheduler" /TR "python C:\path\to\task_scheduler.py --daemon" /SC ONSTART /RU SYSTEM

:: Gmail watcher every minute
schtasks /Create /TN "AI_Employee_Gmail" /TR "python C:\path\to\gmail_watcher.py" /SC MINUTE /MO 2

:: WhatsApp watcher every 30 seconds
schtasks /Create /TN "AI_Employee_WhatsApp" /TR "python C:\path\to\whatsapp_watcher.py" /SC MINUTE /MO 1
```

---

### Option 3: Linux systemd (Production)

Create service file:

```ini
# /etc/systemd/system/ai-employee.service
[Unit]
Description=AI Employee System
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/AI_Employee_Vault/scripts
ExecStart=/usr/bin/python3 task_scheduler.py --daemon
Restart=always
Environment="PATH=/usr/bin:/usr/local/bin"

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable ai-employee
sudo systemctl start ai-employee
sudo systemctl status ai-employee
```

---

### Option 4: PM2 (Cross-Platform Production)

```bash
# Install PM2
npm install -g pm2

# Start all components
cd AI_Employee_Vault/scripts

pm2 start task_scheduler.py --name "ai-scheduler" --interpreter python3
pm2 start gmail_watcher.py --name "ai-gmail" --interpreter python3
pm2 start whatsapp_watcher.py --name "ai-whatsapp" --interpreter python3
pm2 start approval_orchestrator.py --name "ai-approval" --interpreter python3

# Save configuration
pm2 save

# Setup startup
pm2 startup
```

---

## 🔍 Monitoring & Maintenance

### Check System Health

```bash
# Overall health
python error_recovery.py --status

# Audit statistics
python error_recovery.py --stats

# Query audit logs
python error_recovery.py --audit-query 2026-03-30
```

### View Logs

```bash
# Today's logs
tail -f AI_Employee_Vault/logs/task_scheduler_*.log
tail -f AI_Employee_Vault/logs/gmail_watcher_*.log

# Audit logs
cat AI_Employee_Vault/logs/audit/audit_*.jsonl

# Error logs
cat AI_Employee_Vault/logs/errors/errors_*.json
```

### Check Dashboard

Open `AI_Employee_Vault/Dashboard.md` in Obsidian or any text editor.

---

## ❓ Troubleshooting

### "Module not found" Error

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Playwright Browser Issues

```bash
# Reinstall browsers
playwright install chromium --force
```

### Gmail Authentication Fails

```bash
# Clear tokens
rm AI_Employee_Vault/credentials/gmail_token.json

# Re-authenticate
python gmail_watcher.py --auth
```

### WhatsApp QR Code Not Appearing

```bash
# Clear session
python whatsapp_watcher.py --fresh-session --visible
```

### MCP Server Won't Start

```bash
# Install MCP library
pip install mcp

# Test server
python email_mcp_server.py --test
```

### Tasks Not Running

```bash
# Check scheduler logs
cat AI_Employee_Vault/logs/task_scheduler_*.log

# Run manually
python task_scheduler.py --run-once
```

---

## 📖 What Each Component Does

### Watchers (Perception)

| Component | File | What It Does |
|-----------|------|--------------|
| **File Watcher** | `filesystem_watcher.py` | Monitors Inbox/ for new files |
| **Gmail Watcher** | `gmail_watcher.py` | Checks Gmail for unread/important emails |
| **WhatsApp Watcher** | `whatsapp_watcher.py` | Monitors WhatsApp for priority messages |

### Processors (Reasoning)

| Component | File | What It Does |
|-----------|------|--------------|
| **Plan Generator** | `plan_generator.py` | Creates step-by-step task plans |
| **Task Scheduler** | `task_scheduler.py` | Runs scheduled tasks (briefings, updates) |
| **Ralph Wiggum** | `ralph_wiggum.py` | Keeps Qwen working until tasks complete |

### Actions (Hands)

| Component | File | What It Does |
|-----------|------|--------------|
| **Email MCP** | `email_mcp_server.py` | Sends emails via Gmail |
| **Odoo MCP** | `odoo_mcp_server.py` | Manages invoices, payments in Odoo |
| **LinkedIn** | `linkedin_poster.py` | Posts to LinkedIn |

### Workflow

| Component | File | What It Does |
|-----------|------|--------------|
| **Approval Orchestrator** | `approval_orchestrator.py` | Executes approved actions |
| **Dashboard Updater** | `dashboard_updater.py` | Updates status dashboard |
| **Briefing Generator** | `briefing_generator.py` | Creates daily/weekly reports |
| **Error Recovery** | `error_recovery.py` | Handles errors and audit logging |

---

## ✅ Verification Checklist

Run this to verify everything is working:

```bash
cd AI_Employee_Vault/scripts

# 1. Verify all components exist
python verify_silver_gold.py

# 2. Test file watcher (no accounts needed)
python filesystem_watcher.py &
echo "test" > ../Inbox/test.txt
sleep 5
ls ../Needs_Action/

# 3. Test plan generator
python plan_generator.py
ls ../Plans/

# 4. Test scheduler
python task_scheduler.py --status

# 5. Test briefing generator
python briefing_generator.py --type daily
ls ../Briefings/

# 6. Test error recovery
python error_recovery.py --status
```

---

## 🎯 Next Steps

1. **Start with Bronze:** Test file watcher first (no accounts)
2. **Add Gmail:** Most important for email automation
3. **Add WhatsApp:** If you use WhatsApp for business
4. **Add LinkedIn:** For social media automation
5. **Add Odoo:** For full accounting integration

---

## 📞 Support

- **Logs:** `AI_Employee_Vault/logs/`
- **Audit:** `AI_Employee_Vault/logs/audit/`
- **Errors:** `AI_Employee_Vault/logs/errors/`
- **Documentation:** `SILVER_GOLD_SETUP.md`

---

*AI Employee System - Complete Setup Guide*  
*Version: Silver + Gold Tier Complete*
