# Test 04: Task Scheduler

**Priority:** High  
**Time Required:** 10 minutes  
**Accounts Needed:** None  

---

## ✅ What This Tests

The Task Scheduler orchestrates all automated tasks on a schedule, including daily briefings, dashboard updates, and health checks.

**Expected Behavior:**
- Runs scheduled tasks automatically
- Shows task status and next run times
- Executes tasks based on cron-like schedules
- Logs all task executions

---

## 🧪 Test Steps

### Step 1: Check Scheduled Tasks

```bash
cd AI_Employee_Vault/scripts
python task_scheduler.py --status
```

**Expected Output:**
```
Scheduled Tasks:
--------------------------------------------------------------------------------

  Daily Briefing (daily_briefing)
    Schedule: daily 08:00
    Status: enabled
    Last Run: Never
    Next Run: Pending
    Runs: 0 | Failures: 0

  Process Needs Action (process_needs_action)
    Schedule: */30 * * * *
    Status: enabled
    Last Run: Never
    Next Run: Pending
    Runs: 0 | Failures: 0

  Update Dashboard (update_dashboard)
    Schedule: */15 * * * *
    Status: enabled
    Last Run: Never
    Next Run: Pending
    Runs: 0 | Failures: 0

  Weekly Business Audit (weekly_audit)
    Schedule: weekly sunday 22:00
    Status: enabled
    Last Run: Never
    Next Run: Pending
    Runs: 0 | Failures: 0

  Cleanup Old Files (cleanup_old_files)
    Schedule: daily 03:00
    Status: enabled
    Last Run: Never
    Next Run: Pending
    Runs: 0 | Failures: 0

  System Health Check (health_check)
    Schedule: hourly
    Status: enabled
    Last Run: Never
    Next Run: Pending
    Runs: 0 | Failures: 0
```

---

### Step 2: Run Due Tasks Once

```bash
python task_scheduler.py --run-once
```

**Expected Output:**
```
Running scheduled tasks...
No tasks due
```

(This is normal - tasks are scheduled for specific times)

---

### Step 3: Test Manual Task Execution

Manually trigger one of the scheduled tasks:

```bash
# Run dashboard update (normally runs every 15 min)
python dashboard_updater.py

# Check it worked
type ..\Dashboard.md | findstr "last_updated"
```

**Expected:** Dashboard should show current timestamp

---

### Step 4: Check Scheduler Logs

```bash
cd ..\logs
type task_scheduler_*.log | findstr /c:"INFO" /c:"ERROR"
```

**Expected:** Should show initialization and task check logs

---

## ✅ Test Passed If

- [ ] `--status` shows all 6 scheduled tasks
- [ ] All tasks show as "enabled"
- [ ] `--run-once` executes without errors
- [ ] Manual task execution works
- [ ] Logs are being written

---

## ❌ Common Issues

### Issue: "Object of type datetime is not JSON serializable"

**Symptom:**
```
TypeError: Object of type datetime is not JSON serializable
```

**Cause:** Bug in task serialization (already fixed)

**Solution:** Delete `scheduler_config.json` and re-run:
```bash
del ..\scheduler_config.json
python task_scheduler.py --status
```

---

### Issue: Tasks never run

**Cause:** Tasks are scheduled for specific times

**Solution:** This is normal behavior. Use `--run-once` to test, or wait for scheduled time.

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Status shows 6 tasks | ⬜ Pass / ⬜ Fail | |
| All tasks enabled | ⬜ Pass / ⬜ Fail | |
| Run-once works | ⬜ Pass / ⬜ Fail | |
| Manual execution works | ⬜ Pass / ⬜ Fail | |
| Logs are written | ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Once this test passes, move to: **Test 05: Approval Orchestrator**

---

*Test Guide v1.0 - AI Employee System*
