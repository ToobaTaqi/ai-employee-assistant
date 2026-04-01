# Personal AI Employee Hackathon 0 - Project Context

## Project Overview

This directory contains the setup and documentation for **Hackathon 0: Building Autonomous FTEs (Full-Time Equivalent) in 2026**. The project aims to create a "Digital FTE" — an AI agent that proactively manages personal and business affairs 24/7 using a local-first, agent-driven architecture.

### Core Concept

A Digital FTE works ~8,760 hours/year (vs. human's ~2,000) at 85-90% cost reduction. It transforms AI from a chatbot into a proactive business partner that:
- Monitors communications (Gmail, WhatsApp, LinkedIn)
- Manages business tasks and accounting
- Generates proactive reports (e.g., "Monday Morning CEO Briefing")
- Executes actions via human-in-the-loop approval workflows

## Architecture & Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Brain** | Qwen Code | Reasoning engine with Ralph Wiggum persistence loop |
| **Memory/GUI** | Obsidian (Markdown) | Local dashboard and long-term memory |
| **Senses (Watchers)** | Python scripts | Monitor Gmail, WhatsApp, filesystems |
| **Hands (MCP)** | Model Context Protocol servers | External actions (email, browser, payments) |
| **Browser Automation** | Playwright MCP | Web navigation, form filling, data extraction |

### Key Patterns

1. **Watcher Architecture**: Lightweight Python scripts run continuously, creating `.md` files in `/Needs_Action` folder when events occur
2. **Human-in-the-Loop**: Sensitive actions require approval via file movement (`/Pending_Approval` → `/Approved`)
3. **Ralph Wiggum Loop**: Stop hook keeps Qwen iterating until multi-step tasks complete
4. **File-Based Orchestration**: Agents communicate by writing/reading markdown files

## Directory Structure

```
hackathon0/
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md  # Main blueprint
├── skills-lock.json          # Qwen skills configuration
├── QWEN.md                   # This file - project context
└── .qwen/
    └── skills/
        └── browsing-with-playwright/  # Browser automation skill
            ├── SKILL.md               # Usage documentation
            ├── references/
            │   └── playwright-tools.md  # MCP tool reference
            └── scripts/
                ├── mcp-client.py       # MCP client for tool calls
                ├── start-server.sh     # Start Playwright MCP server
                ├── stop-server.sh      # Stop server gracefully
                └── verify.py           # Server health check
```

## Available Skills

### browsing-with-playwright

Browser automation via Playwright MCP server for web navigation, form submission, and data extraction.

**Server Management:**
```bash
# Start server
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Stop server
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh

# Verify server
python3 .qwen/skills/browsing-with-playwright/scripts/verify.py
```

**Key Tools:**
- `browser_navigate` - Navigate to URL
- `browser_snapshot` - Capture accessibility snapshot (preferred over screenshots)
- `browser_click` / `browser_type` / `browser_fill_form` - Interact with elements
- `browser_run_code` - Execute complex Playwright workflows
- `browser_take_screenshot` - Capture visual screenshot

See `.qwen/skills/browsing-with-playwright/SKILL.md` for detailed usage.

## Hackathon Tiers

| Tier | Time | Deliverables | Status |
|------|------|------------|--------|
| **Bronze** | 8-12 hrs | Obsidian vault, 1 Watcher, Qwen reading/writing | ✅ COMPLETE |
| **Silver** | 20-30 hrs | Multiple Watchers, MCP server, HITL workflow, scheduling | Pending |
| **Gold** | 40+ hrs | Full integration, Odoo accounting, social media, Ralph Wiggum loop | Pending |
| **Platinum** | 60+ hrs | Cloud deployment, dual-agent (Cloud/Local), A2A messaging | Pending |

### Bronze Tier - Completed Deliverables

**Location:** `AI_Employee_Vault/`

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status dashboard
├── Company_Handbook.md       # Rules of engagement & business goals
├── QWEN_INTEGRATION.md       # Guide for Qwen Code usage
├── Inbox/                    # Drop zone for new items
├── Needs_Action/             # Tasks awaiting processing
├── Done/                     # Completed tasks
├── Pending_Approval/         # Awaiting human decision
├── Approved/                 # Approved actions
├── Rejected/                 # Rejected actions
├── Briefings/                # Generated reports
├── Plans/                    # Task plans
├── Accounting/               # Financial records
├── Updates/                  # Status updates
├── Processing/               # Files being processed
├── logs/                     # Watcher logs
└── scripts/
    ├── base_watcher.py       # Abstract base class for watchers
    ├── filesystem_watcher.py # File drop monitoring (Bronze Watcher)
    ├── verify_bronze.py      # Bronze tier verification script
    └── requirements.txt      # Python dependencies
```

**How to use:**

```bash
# 1. Install dependencies
cd AI_Employee_Vault/scripts
pip install -r requirements.txt

# 2. Start the File System Watcher
python filesystem_watcher.py

# 3. Drop files into AI_Employee_Vault/Inbox/
# Watcher will create action files in Needs_Action/

# 4. Verify Bronze tier completion
python verify_bronze.py

# 5. Use Qwen Code to process tasks
cd ..
qwen  # Then prompt to read/process Needs_Action folder
```

## Key Files

| File | Purpose |
|------|---------|
| `Personal AI Employee Hackathon 0_...md` | Complete architectural blueprint with templates, code examples, and tier requirements |
| `skills-lock.json` | Tracks installed Qwen skills and their versions |
| `.qwen/skills/browsing-with-playwright/SKILL.md` | Browser automation usage guide |
| `.qwen/skills/browsing-with-playwright/references/playwright-tools.md` | Complete MCP tool schema reference |

## Usage Guidelines

### For This Project

1. **Read the blueprint**: The main `.md` file contains comprehensive architecture, code templates, and requirements
2. **Use Playwright skill**: Invoke via `skill: "browsing-with-playwright"` for any web automation tasks
3. **Follow Obsidian conventions**: Use markdown files for state management (`/Inbox`, `/Needs_Action`, `/Done`)
4. **Implement Watchers**: Python scripts should follow the `BaseWatcher` pattern in the blueprint

### Development Conventions

- **Local-first**: All data stored in local Obsidian vault (privacy-focused)
- **File-based communication**: Agents coordinate via markdown files, not databases
- **Human approval required**: Sensitive actions (payments, sending messages) require explicit approval
- **Audit logging**: All actions should be logged for accountability

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Qwen Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts |
| Node.js | v24+ LTS | MCP servers |
| GitHub Desktop | Latest | Version control |

## External Resources

- **Wednesday Research Meetings**: Zoom meetings for collaborative learning (see blueprint for link)
- **Ralph Wiggum Plugin**: Custom stop hook for persistent task completion
- **MCP Servers**: filesystem, email-mcp, browser-mcp, calendar-mcp, slack-mcp

## Notes for AI Assistants

When working on this project:
1. Reference the main blueprint document for architecture decisions
2. Use the Playwright skill for any web interaction tasks
3. Follow the file-based orchestration pattern (Watchers → Needs_Action → Qwen → Approval → Done)
4. Prioritize human-in-the-loop patterns for sensitive operations
5. Implement the Ralph Wiggum loop for multi-step autonomous tasks
