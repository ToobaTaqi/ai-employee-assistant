# Test 05: Approval Orchestrator

**Priority:** High  
**Time Required:** 15 minutes  
**Accounts Needed:** None  

---

## ✅ What This Tests

The Approval Orchestrator implements the Human-in-the-Loop (HITL) workflow. It watches `/Approved` and `/Rejected` folders and executes actions when files are moved there.

**Expected Behavior:**
- Monitors Approved/Rejected folders
- Executes actions when files are moved to Approved
- Logs rejections when files are moved to Rejected
- Moves processed files to Done

---

## 🧪 Test Steps

### Step 1: Create Test Approval File

Create a test approval request file:

```bash
cd AI_Employee_Vault

# Create test approval file
echo --- > Pending_Approval\TEST_Approval.md
echo type: approval_request >> Pending_Approval\TEST_Approval.md
echo action: generic >> Pending_Approval\TEST_Approval.md
echo test: true >> Pending_Approval\TEST_Approval.md
echo --- >> Pending_Approval\TEST_Approval.md
echo. >> Pending_Approval\TEST_Approval.md
echo # Test Approval Request >> Pending_Approval\TEST_Approval.md
echo. >> Pending_Approval\TEST_Approval.md
echo Move to Approved to test the orchestrator. >> Pending_Approval\TEST_Approval.md
```

**Verify file created:**
```bash
type Pending_Approval\TEST_Approval.md
```

---

### Step 2: Start Approval Orchestrator

```bash
cd scripts
python approval_orchestrator.py --interval 5
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════╗
║         Approval Workflow Orchestrator                    ║
╠══════════════════════════════════════════════════════════╣
║  Vault Path: C:\...\AI_Employee_Vault
║  Check Interval: 5s
║                                                            ║
║  Monitoring folders:                                       ║
║    - /Approved (execute actions)                           ║
║    - /Rejected (log rejections)                            ║
║                                                            ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝

2026-03-31 XX:XX:XX - ApprovalOrchestrator - INFO - Approval Orchestrator initialized
2026-03-31 XX:XX:XX - ApprovalOrchestrator - INFO - Starting Approval Orchestrator
```

Leave this running in the terminal.

---

### Step 3: Approve the Test File

In a **new terminal**, move the test file to Approved:

```bash
cd AI_Employee_Vault
move Pending_Approval\TEST_Approval.md Approved\
```

---

### Step 4: Check Orchestrator Output

Switch back to the orchestrator terminal. You should see:

```
2026-03-31 XX:XX:XX - ApprovalOrchestrator - INFO - Found approved action: generic
2026-03-31 XX:XX:XX - ApprovalOrchestrator - INFO - Executing approved action: generic
2026-03-31 XX:XX:XX - ApprovalOrchestrator - INFO - Action result: True
2026-03-31 XX:XX:XX - ApprovalOrchestrator - INFO - Moved to Done: TEST_Approval_20260331_XXXXXX.md_rejected
```

---

### Step 5: Verify File Moved to Done

```bash
dir Done\TEST_*.md
```

**Expected:** File should be in Done folder with timestamp

---

### Step 6: Stop Orchestrator

Press `Ctrl+C` in the orchestrator terminal to stop it.

---

### Step 7: Check Approval Logs

```bash
cd logs
type approval_*.json
```

**Expected:** Should show the action execution log

---

## ✅ Test Passed If

- [x] Orchestrator starts without errors
- [x] Detects file moved to Approved
- [x] Executes the action (generic action logs success)
- [x] Moves file to Done folder
- [x] Logs the execution

---

## ❌ Common Issues

### Issue: File not detected

**Cause:** Check interval too long

**Solution:** Use `--interval 5` for faster detection during testing

---

### Issue: Action fails to execute

**Cause:** Unknown action type

**Solution:** Use `action: generic` for testing - it always succeeds

---

### Issue: File not moved

**Cause:** File lock or permission issue

**Solution:** Close any editors that have the file open, retry

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Orchestrator starts | ⬜ Pass / ⬜ Fail | |
| Detects approved file | ⬜ Pass / ⬜ Fail | |
| Executes action | ⬜ Pass / ⬜ Fail | |
| Moves file to Done | ⬜ Pass / ⬜ Fail | |
| Logs execution | ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Once this test passes, move to: **Test 06: Email MCP Server** (requires Gmail API)

---

*Test Guide v1.0 - AI Employee System*
