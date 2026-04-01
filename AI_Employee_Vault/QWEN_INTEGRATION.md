# Qwen Code Integration Guide

## Overview

This guide explains how to integrate Qwen Code with your Obsidian vault for the AI Employee system. Qwen Code acts as the "brain" that reads tasks, reasons about them, and writes results.

## Setup

### 1. Configure Qwen Code

Ensure Qwen Code is installed and configured:

```bash
# Verify installation
qwen --version

# Navigate to your vault
cd path/to/AI_Employee_Vault
```

### 2. Start Qwen Code in Vault Directory

```bash
# Start Qwen Code pointed at your vault
qwen
```

## Reading from the Vault

### Check for New Tasks

Use these prompts to have Qwen read and process tasks:

```
Check the /Needs_Action folder for any new files that need processing.
Read each file and create a summary of what actions are required.
```

### Read Specific File Types

```
Read all files in /Needs_Action that are type: file_drop
Summarize what each file needs.
```

### Full Vault Audit

```
Perform a full audit of the vault:
1. Check /Inbox for new items
2. Check /Needs_Action for pending tasks
3. Review /Pending_Approval for decisions needed
4. Update Dashboard.md with current status
```

## Writing to the Vault

### Create Action Plans

After reading tasks, Qwen should create plans:

```markdown
# /Plans/Plan_YYYY-MM-DD_TaskName.md

---
type: plan
created: 2026-03-05T10:00:00Z
status: in_progress
priority: high
---

## Objective

[Clear statement of what needs to be accomplished]

## Steps

- [ ] Step 1: Description
- [ ] Step 2: Description
- [ ] Step 3: Description

## Resources

- Links to relevant files
- Reference documents

## Notes

[Additional context]
```

### Update Dashboard

```
Update Dashboard.md with:
- Count of items in each folder
- Summary of completed tasks
- Current financial status
- Any alerts or notifications
```

### Create Approval Requests

For sensitive actions, create approval files:

```markdown
# /Pending_Approval/APPROVAL_Action_Description_Date.md

---
type: approval_request
action: [action_type]
created: 2026-03-05T10:00:00Z
status: pending
expires: 2026-03-06T10:00:00Z
---

## Action Required

[Description of what needs approval]

## Details

| Property | Value |
|----------|-------|
| Amount | $XXX |
| Recipient | [Name] |
| Reason | [Purpose] |

## To Approve

Move this file to `/Approved` folder.

## To Reject

Move this file to `/Rejected` folder with a note explaining why.
```

### Move Completed Tasks

```
Move processed task files from /Needs_Action to /Done
Update the file with completion timestamp and summary.
```

## Workflow Examples

### Example 1: Process Dropped File

**User prompt:**
```
Process all files in /Needs_Action that are type: file_drop.
For each file:
1. Read and understand the content
2. Perform the suggested actions
3. Move to /Done when complete
4. Update Dashboard.md
```

**Expected Qwen behavior:**
1. Reads each file_drop action file
2. Opens the referenced file from /Processing
3. Performs requested analysis/summary
4. Writes results to the action file
5. Moves file to /Done
6. Updates Dashboard.md

### Example 2: Generate Daily Briefing

**User prompt:**
```
Generate a daily briefing for today.
Include:
- Tasks completed yesterday
- Pending tasks
- Financial summary
- Upcoming deadlines
Save to /Briefings/
```

### Example 3: Handle Approval Request

**User prompt:**
```
Check /Pending_Approval for any items awaiting my decision.
Summarize each item and wait for my approval.
```

## Best Practices

### 1. Always Update Status

After processing any task:
- Update the file with completion status
- Move to appropriate folder (/Done, /Pending_Approval, etc.)
- Update Dashboard.md

### 2. Use YAML Frontmatter

All files should have frontmatter for easy filtering:

```yaml
---
type: [task_type]
status: [pending|in_progress|completed|approved|rejected]
created: ISO8601_timestamp
priority: [low|medium|high|critical]
---
```

### 3. Be Explicit About Actions

When Qwen completes an action, document it:

```markdown
## Actions Taken

- [x] Read file content (2026-03-05T10:30:00Z)
- [x] Summarized key points (2026-03-05T10:35:00Z)
- [x] Categorized as "Invoice" (2026-03-05T10:36:00Z)
- [x] Moved to /Done (2026-03-05T10:37:00Z)
```

### 4. Handle Errors Gracefully

If Qwen encounters an error:

```markdown
## Error Log

| Timestamp | Error | Resolution |
|-----------|-------|------------|
| 2026-03-05T10:00:00Z | File not found | Flagged for manual review |
```

Move problematic files to `/Needs_Action/Errors/` for manual review.

### 5. Maintain Audit Trail

Never delete files. Instead:
- Move to /Done when complete
- Add completion notes
- Keep for 30 days minimum

## Automation Scripts

### Run Qwen Code with Specific Task

Create a script to automate Qwen:

```bash
#!/bin/bash
# run_task.sh

VAULT_PATH="/path/to/AI_Employee_Vault"
TASK="$1"

cd "$VAULT_PATH"
echo "$TASK" | qwen
```

### Scheduled Briefing Generation

Use cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Daily briefing at 8 AM
0 8 * * * cd /path/to/AI_Employee_Vault && echo "Generate daily briefing" | qwen
```

## Troubleshooting

### Qwen Can't Find Files

**Problem:** Qwen reports files don't exist

**Solution:**
- Verify you're in the correct directory
- Use absolute paths in prompts
- Check file permissions

### Qwen Forgets Context

**Problem:** Qwen loses track of multi-step tasks

**Solution:**
- Use Ralph Wiggum loop for persistence
- Break tasks into smaller prompts
- Write intermediate state to files

### Files Not Being Processed

**Problem:** Watcher creates files but Qwen doesn't process them

**Solution:**
- Ensure Qwen is running in the vault directory
- Check that file frontmatter is correct
- Verify Qwen has read permissions

## Next Steps

After mastering basic integration:

1. **Implement Ralph Wiggum Loop** - For autonomous multi-step tasks
2. **Add MCP Servers** - For external actions (email, browser, payments)
3. **Create More Watchers** - Gmail, WhatsApp, etc.
4. **Set Up Scheduling** - Automated briefings and audits

---

*For more details, see the main blueprint document.*
