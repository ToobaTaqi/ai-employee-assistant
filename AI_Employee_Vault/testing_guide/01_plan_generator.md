# Test 01: Plan Generator

**Priority:** High  
**Time Required:** 10 minutes  
**Accounts Needed:** None  

---

## ✅ What This Tests

The Plan Generator automatically creates structured task plans for items in the `Needs_Action/` folder.

**Expected Behavior:**
- Reads all action files from `Needs_Action/`
- Creates detailed plan files in `Plans/` folder
- Each plan includes steps, time estimates, and success criteria

---

## 🧪 Test Steps

### Step 1: Check Prerequisites

```bash
cd AI_Employee_Vault/scripts
```

Make sure there are action files to process:

```bash
# Check Needs_Action folder
dir ..\Needs_Action\*.md
```

**Expected:** You should see several `.md` files (from Gmail/WhatsApp watchers)

---

### Step 2: Run Plan Generator

```bash
python plan_generator.py
```

**Expected Output:**
```
Generating plans for all pending actions...
Generated plan: PLAN_Verify your email address_20260331_131846.md
Generated plan: PLAN_Docker You Docker Ready_20260331_131846.md
...
✓ Generated XX plan(s)
```

---

### Step 3: Verify Plans Created

```bash
# Check Plans folder
dir ..\Plans\*.md
```

**Expected:** New plan files should appear with timestamps

---

### Step 4: Inspect a Plan File

Open any plan file in Obsidian or a text editor:

```bash
# View first plan (adjust filename)
type ..\Plans\PLAN_Ammi_*.md
```

**Expected Content:**
```markdown
---
id: PLAN_Ammi_20260331_131846
type: plan
created: 2026-03-31T13:18:46
status: pending
priority: high
...
---

# Task Plan: Ammi

## Overview
| Property | Value |
|----------|-------|
| Task Type | whatsapp |
| Priority | HIGH |
| Estimated Time | 10 minutes |
| Requires Approval | Yes |

## Execution Steps
- [ ] Step 1: Read and understand email content
- [ ] Step 2: Identify sender intent
...
```

---

## ✅ Test Passed If

- [ ] Plan Generator runs without errors
- [ ] Plans are created in `Plans/` folder
- [ ] Plan files have valid markdown structure
- [ ] Plans include steps, priority, and time estimates

---

## ❌ Common Issues

### Issue: "Invalid argument" error

**Symptom:**
```
Error generating plan: [Errno 22] Invalid argument: '...\Plans\PLAN_...\ntype.md'
```

**Cause:** Filename contains newline characters

**Solution:** Already fixed in latest version. Re-run the test.

---

### Issue: No plans generated

**Symptom:**
```
✓ Generated 0 plan(s)
```

**Cause:** No action files in `Needs_Action/`

**Solution:** 
1. Drop a test file in `Inbox/`
2. Run Filesystem Watcher to create action file
3. Re-run Plan Generator

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Script runs without errors | ⬜ Pass / ⬜ Fail | |
| Plans created in Plans/ | ⬜ Pass / ⬜ Fail | |
| Plans have valid structure | ⬜ Pass / ⬜ Fail | |
| Includes execution steps | ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Once this test passes, move to: **Test 02: Dashboard Updater**

---

*Test Guide v1.0 - AI Employee System*
