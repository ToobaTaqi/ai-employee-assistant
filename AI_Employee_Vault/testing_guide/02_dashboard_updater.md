# Test 02: Dashboard Updater

**Priority:** High  
**Time Required:** 5 minutes  
**Accounts Needed:** None  

---

## ✅ What This Tests

The Dashboard Updater refreshes the main `Dashboard.md` with current system status, pending tasks count, and financial summary.

**Expected Behavior:**
- Counts files in each folder
- Updates status table
- Shows recent completed tasks
- Displays financial snapshot

---

## 🧪 Test Steps

### Step 1: Run Dashboard Updater

```bash
cd AI_Employee_Vault/scripts
python dashboard_updater.py
```

**Expected Output:**
```
✓ Dashboard updated at 13:19:34
```

---

### Step 2: Check Dashboard File

Open `Dashboard.md` in Obsidian or text editor:

```bash
type ..\Dashboard.md
```

**Expected Content:**
```markdown
---
type: dashboard
last_updated: 2026-03-31T13:19:34
status: active
---

# AI Employee Dashboard

> **Last Updated:** 2026-03-31
> **Status:** Active Monitoring

---

## 📊 Quick Status

| Metric | Value |
|--------|-------|
| Pending Tasks | XX |
| Awaiting Approval | XX |
| Completed Today | XX |
| Revenue MTD | $X,XXX.XX |

---

## 📥 Inbox Summary

*Check Inbox folder for new items*

---

## ⏳ Needs Action

**XX items pending**

...
```

---

### Step 3: Verify Counts Match

Manually count files and compare:

```bash
# Count files in each folder
echo "Needs_Action:"
dir ..\Needs_Action\*.md | findstr /c:"File(s)"

echo "Done:"
dir ..\Done\*.md | findstr /c:"File(s)"

echo "Pending_Approval:"
dir ..\Pending_Approval\*.md | findstr /c:"File(s)"
```

**Expected:** Numbers should match Dashboard values

---

## ✅ Test Passed If

- [x] Dashboard Updater runs without errors
- [x] Dashboard.md is updated with current timestamp
- [x] File counts are accurate
- [x] Financial summary is displayed
- [x] Formatting is clean and readable

---

## ❌ Common Issues

### Issue: Dashboard shows 0 for everything

**Cause:** No files in folders yet

**Solution:** This is normal for fresh installs. Run other watchers first to create some data.

---

### Issue: Financial summary shows $0

**Cause:** No accounting transactions recorded yet

**Solution:** Normal - accounting integration requires Odoo setup (Gold tier)

---

## 📊 Test Results

| Check                      | Status          | Notes |
| -------------------------- | --------------- | ----- |
| Script runs without errors | ⬜ Pass / ⬜ Fail |       |
| Dashboard updated          | ⬜ Pass / ⬜ Fail |       |
| Timestamp is current       | ⬜ Pass / ⬜ Fail |       |
| File counts accurate       | ⬜ Pass / ⬜ Fail |       |
| Formatting is clean        | ⬜ Pass / ⬜ Fail |       |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Once this test passes, move to: **Test 03: Briefing Generator**

---

*Test Guide v1.0 - AI Employee System*
