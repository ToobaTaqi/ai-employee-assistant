# AI Employee System - Complete Guide

> **Your Personal AI Employee - Local-First, Agent-Driven, Human-in-the-Loop**

**Status:** ✅ Silver + Gold Tier Complete  
**Last Updated:** March 30, 2026

---

## 🚀 Quick Start (60 Seconds)

```bash
# 1. Install dependencies
cd AI_Employee_Vault/scripts
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Verify installation
python verify_silver_gold.py

# 4. Start the system
python task_scheduler.py --daemon
```

**That's it!** The system is running. See [QUICK_START.md](QUICK_START.md) for more.

> **Note:** The task scheduler runs in the background checking for tasks every minute. Press `Ctrl+C` to stop.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[QUICK_START.md](QUICK_START.md)** | ⭐ Start here - 1-page reference |
| **[README_SETUP.md](README_SETUP.md)** | Complete setup & testing guide |
| **[SILVER_GOLD_SETUP.md](SILVER_GOLD_SETUP.md)** | Silver/Gold tier configuration |
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | What was built |
| **[QWEN_INTEGRATION.md](QWEN_INTEGRATION.md)** | Qwen Code usage |
| **[Company_Handbook.md](Company_Handbook.md)** | Business rules |
| **[Dashboard.md](Dashboard.md)** | Real-time status |

---

## 🎯 Do I Need Accounts?

| To Test | Accounts Needed |
|---------|-----------------|
| **Basic functionality** | ❌ None - File watcher works without accounts |
| **Email automation** | ✅ Gmail account |
| **WhatsApp monitoring** | ✅ WhatsApp (via QR login) |
| **LinkedIn posting** | ✅ LinkedIn |
| **Accounting** | ✅ Odoo ERP |

**Short answer:** Start without accounts to test, add Gmail first for full email features.

---

## 🧪 Quick Test (No Accounts)

```bash
# 1. Start watcher
cd AI_Employee_Vault/scripts
python filesystem_watcher.py

# 2. Drop a file (in another terminal)
echo "Test content" > ../Inbox/test.txt

# 3. Check for action file
ls ../Needs_Action/
```

✅ If you see a new `.md` file, the system is working!

---

## What is the AI Employee?

The Bronze Tier is the **foundation** of your Personal AI Employee system. It establishes the basic infrastructure for:

1. **Perception** - Watching for new tasks (via File System Watcher)
2. **Memory** - Storing information locally (via Obsidian vault)
3. **Reasoning** - Processing tasks with AI (via Qwen Code)

Think of it as hiring an employee who can:
- Notice when you give them new work (dropping files)
- Read and understand the work
- Tell you what they plan to do
- Wait for your approval on important decisions

---

## Why These Tools and Approaches?

### 1. **Obsidian (Markdown Files) for Memory**

**Why not a database?**
- **Human-readable**: You can open any file and understand it without special software
- **Version control friendly**: Markdown works great with Git
- **No setup required**: No database server, no migrations
- **Portable**: Files work on any computer, any OS
- **AI-friendly**: LLMs understand Markdown structure naturally

**Why local-first?**
- **Privacy**: Your data stays on your machine
- **No API limits**: Unlimited reads/writes
- **Works offline**: No internet required for core functionality
- **Fast**: No network latency

### 2. **File System Watcher for Perception**

**Why not just prompt Qwen directly?**
- **Autonomy**: The system can work without you remembering to trigger it
- **Continuous monitoring**: Watches 24/7 for new work
- **Decoupled**: Watcher and AI can run independently
- **Audit trail**: Every detected item creates a record

**Why file-based triggers?**
- **Simple**: No message queues, no complex infrastructure
- **Debuggable**: You can see exactly what was detected
- **Reliable**: Files don't disappear if a process crashes

### 3. **Qwen Code for Reasoning**

**Why an AI agent?**
- **Understanding**: Can read any document and extract meaning
- **Flexibility**: Handles unexpected tasks without reprogramming
- **Natural language**: You communicate in English, not code
- **Planning**: Can break complex tasks into steps

### 4. **Folder-Based Workflow**

```
Inbox → Needs_Action → [Processing] → Done
                         ↓
                  Pending_Approval → Approved/Rejected
```

**Why folders?**
- **Visual status**: You can see workload at a glance
- **Simple state machine**: Folder = status
- **No database queries**: Just list files
- **Human-in-the-loop**: Move to Approved to authorize actions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR AI EMPLOYEE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │  PERCEPTION  │────▶│   REASONING  │────▶│    ACTION    │ │
│  │   Watchers   │     │  Qwen Code   │     │   Qwen + MCP │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │ Inbox/       │     │ Needs_Action/│     │ Done/        │ │
│  │ (Drop zone)  │     │ (To process) │     │ (Completed)  │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│                              │                               │
│                              ▼                               │
│                       ┌──────────────┐                       │
│                       │ Pending_     │                       │
│                       │ Approval/    │                       │
│                       │ (Wait for    │                       │
│                       │  human)      │                       │
│                       └──────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## File-by-File Guide

### Root Files

| File | Purpose |
|------|---------|
| `Dashboard.md` | **Real-time status display** - Shows pending tasks, completed work, financial summary. Updated by Qwen after each processing session. Think of it as your employee's daily report. |
| `Company_Handbook.md` | **Rules and guidelines** - Contains your business rules, communication style, spending limits, and escalation procedures. Qwen reads this to know how to behave. |
| `QWEN_INTEGRATION.md` | **Usage guide for Qwen** - Instructions for how Qwen should read/write to the vault. Contains example prompts and workflows. |

### Folders

| Folder | Purpose | Example Contents |
|--------|---------|------------------|
| `Inbox/` | **Drop zone for new work** - Put files here when you want them processed | `invoice.pdf`, `client_email.txt` |
| `Needs_Action/` | **Tasks awaiting processing** - Watcher creates action files here | `FILE_invoice_20260305.md` |
| `Done/` | **Completed tasks** - Files moved here after processing | `FILE_invoice_processed.md` |
| `Pending_Approval/` | **Awaiting your decision** - Qwen creates files here for sensitive actions | `APPROVAL_Payment_Vendor.md` |
| `Approved/` | **Authorized actions** - Move files here to approve | (You move files here) |
| `Rejected/` | **Declined actions** - Move files here to reject | (You move files here) |
| `Processing/` | **Files being worked on** - Copies of dropped files during processing | `invoice.pdf` (copy) |
| `Briefings/` | **Generated reports** - Daily/weekly summaries by Qwen | `2026-03-05_Briefing.md` |
| `Plans/` | **Task plans** - Step-by-step plans created by Qwen | `Plan_ClientOnboarding.md` |
| `Accounting/` | **Financial records** - Transaction logs, expense tracking | `Transactions_March.md` |
| `Updates/` | **Status updates** - Change logs and notifications | `Update_2026-03-05.md` |
| `logs/` | **Watcher logs** - Technical logs for debugging | `filesystem_watcher_20260305.log` |

### Scripts

| File | Purpose | How to Use |
|------|---------|------------|
| `scripts/base_watcher.py` | **Base class for all watchers** - Provides common functionality (logging, file creation, deduplication) | Don't run directly. Extend it to create new watchers (Gmail, WhatsApp, etc.) |
| `scripts/filesystem_watcher.py` | **File drop monitor** - Watches Inbox/ for new files and creates action files | Run: `python filesystem_watcher.py` |
| `scripts/verify_bronze.py` | **Bronze tier checker** - Verifies all required files and folders exist | Run: `python verify_bronze.py` |
| `scripts/requirements.txt` | **Python dependencies** - Lists required packages | Install: `pip install -r requirements.txt` |

---

## How It Works: Step by Step

### Scenario: Processing an Invoice

**Step 1: You drop a file**
```
You copy "invoice_acme.pdf" into AI_Employee_Vault/Inbox/
```

**Step 2: Watcher detects it**
```
[Watcher log] Found new file: invoice_acme.pdf (46 KB)
[Watcher log] Created: FILE_invoice_acme_md5hash_20260305_143022.md
```

**Step 3: Action file created in Needs_Action/**
```markdown
---
type: file_drop
original_name: invoice_acme.pdf
file_category: document
status: pending
---

# File Dropped for Processing

## Suggested Actions
- [ ] Read and summarize content
- [ ] Extract vendor and amount
- [ ] Categorize expense
- [ ] Schedule payment if approved
```

**Step 4: You ask Qwen to process**
```bash
qwen
> "Please process all files in Needs_Action folder"
```

**Step 5: Qwen reads and acts**
- Opens the PDF from Processing/
- Extracts: Vendor=ACME Corp, Amount=$500, Due=2026-03-15
- Creates expense entry in Accounting/
- Since amount > $500 threshold, creates approval request

**Step 6: Approval request created**
```markdown
# /Pending_Approval/APPROVAL_Payment_ACME_2026-03-05.md

## Action Required
Pay invoice from ACME Corp

## Details
| Amount | $500.00 |
| Vendor | ACME Corp |
| Due Date | 2026-03-15 |

## To Approve
Move this file to /Approved folder.
```

**Step 7: You approve**
```
You move the file from Pending_Approval/ to Approved/
```

**Step 8: Qwen completes the task**
- Processes payment (via MCP server in future tiers)
- Moves original action file to Done/
- Updates Dashboard.md

---

## Why This Design?

### Problem: AI Agents Are Lazy
**Solution:** Watchers provide continuous perception. The AI doesn't need to remember to check - it gets notified.

### Problem: AI Makes Mistakes
**Solution:** Human-in-the-loop via approval folders. Sensitive actions require explicit approval.

### Problem: AI Forgets Multi-Step Tasks
**Solution:** File-based state. Even if Qwen stops, the files remain and can be resumed.

### Problem: Black Box Decisions
**Solution:** Every action is documented in Markdown. You can audit what happened and why.

### Problem: Vendor Lock-in
**Solution:** All data is plain text Markdown. You can switch AI providers anytime.

---

## Extending Beyond Bronze

### Silver Tier Adds:
- Gmail Watcher (email monitoring)
- WhatsApp Watcher (message monitoring)
- MCP Server for sending emails
- Scheduled tasks (cron)

### Gold Tier Adds:
- Odoo accounting integration
- Social media posting
- Ralph Wiggum persistence loop
- Comprehensive error handling

### Platinum Tier Adds:
- Cloud deployment (24/7 operation)
- Dual-agent architecture (Cloud + Local)
- Advanced synchronization

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Watcher doesn't detect files | Check that Inbox/ path is correct. Verify file permissions. |
| Qwen can't read files | Ensure you're running Qwen in the vault directory. Check file permissions. |
| Action files not created | Check watcher logs in logs/ folder. Verify Python dependencies installed. |
| Qwen makes wrong decisions | Update Company_Handbook.md with clearer rules. Use approval workflow. |

---

## Key Principles

1. **Local-First**: Your data stays on your machine
2. **Human-in-the-Loop**: Important decisions require approval
3. **File-Based State**: Folders represent workflow status
4. **Audit Everything**: Every action is logged
5. **Plain Text**: Markdown ensures portability and readability

---

*For more details, see QWEN_INTEGRATION.md and the main blueprint document.*
