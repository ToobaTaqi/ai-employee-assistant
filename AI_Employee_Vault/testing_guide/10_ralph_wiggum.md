# Test 10: Ralph Wiggum Persistence Loop

**Priority:** Medium  
**Time Required:** 15 minutes  
**Accounts Needed:** None  

---

## ✅ What This Tests

The Ralph Wiggum loop keeps Qwen Code working on multi-step tasks until completion, preventing the "lazy agent" problem.

**Expected Behavior:**
- Creates state files for tasks
- Monitors task completion
- Re-injects prompts if task incomplete
- Stops when task moves to Done

---

## 🧪 Test Steps

### Step 1: Create Test Task

```bash
cd AI_Employee_Vault

# Create a test task file
echo --- > Needs_Action\TEST_Ralph_Task.md
echo type: test >> Needs_Action\TEST_Ralph_Task.md
echo priority: medium >> Needs_Action\TEST_Ralph_Task.md
echo --- >> Needs_Action\TEST_Ralph_Task.md
echo >> Needs_Action\TEST_Ralph_Task.md
echo # Test Task for Ralph Wiggum >> Needs_Action\TEST_Ralph_Task.md
echo >> Needs_Action\TEST_Ralph_Task.md
echo Please process this test file and move it to Done when complete. >> Needs_Action\TEST_Ralph_Task.md
```

---

### Step 2: Run Ralph Wiggum Loop

```bash
cd scripts
python ralph_wiggum.py --run-loop "Process the TEST_Ralph_Task.md file in Needs_Action folder. Analyze it, create a plan, and move to Done when complete."
```

**Expected Output:**
```
Starting Ralph Wiggum loop...
Task: Process the TEST_Ralph_Task.md file...
Max iterations: 10

Loop completed!
  Iterations: X
  Duration: XX.Xs
  Status: completed
```

---

### Step 3: Check State File

```bash
type ..\Processing\ralph_state.json
```

**Expected:**
```json
{
  "prompt": "Process the TEST_Ralph_Task.md file...",
  "task_file": "TEST_Ralph_Task.md",
  "status": "completed",
  "completion_detected": true,
  "iteration": X
}
```

---

### Step 4: Verify Task Completed

```bash
dir ..\Done\TEST_Ralph_Task*.md
```

**Expected:** File should be moved to Done folder

---

## ✅ Test Passed If

- [ ] Loop starts without errors
- [ ] Task is processed
- [ ] State file created and updated
- [ ] Task file moved to Done
- [ ] Loop exits on completion

---

## ❌ Common Issues

### Issue: Qwen Code not found

**Symptom:**
```
ERROR: Qwen Code not installed
```

**Solution:** Install Qwen Code or skip this test

---

### Issue: Loop runs forever

**Cause:** Task completion not detected

**Solution:** Press Ctrl+C, check if task file was processed

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Loop starts | ⬜ Pass / ⬜ Fail | |
| Task processed | ⬜ Pass / ⬜ Fail | |
| State file created | ⬜ Pass / ⬜ Fail | |
| Task moved to Done | ⬜ Pass / ⬜ Fail | |
| Loop exits cleanly | ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Move to: **Test 11: Error Recovery System**

---

*Test Guide v1.0 - AI Employee System*
