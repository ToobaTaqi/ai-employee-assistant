# Test 06: Email MCP Server

**Priority:** High  
**Time Required:** 20 minutes  
**Accounts Needed:** Gmail API credentials  

---

## ⚠️ Prerequisites

Before testing, you need:
1. Google Cloud project with Gmail API enabled
2. OAuth2 credentials (credentials.json)
3. Completed OAuth authentication

If not set up yet, complete **Test 07: Gmail Watcher** first which includes setup instructions.

---

## ✅ What This Tests

The Email MCP Server provides email sending capabilities via Gmail API with Human-in-the-Loop approval workflow.

**Expected Behavior:**
- Connects to Gmail API
- Can send emails
- Can create drafts
- Can search emails
- Logs all actions

---

## 🧪 Test Steps

### Step 1: Verify Credentials

```bash
cd AI_Employee_Vault
dir credentials\credentials.json
```

**Expected:** File should exist

If not, follow Gmail Watcher setup guide first.

---

### Step 2: Test Email Server Connection

```bash
cd scripts
python ..\mcp_servers\email_mcp_server.py --test

python ..\mcp_servers\email_mcp_server.py --auth # run this if not authenticated
```

**Expected Output:**
```json
{
  "success": true,
  "dry_run": true,
  "message": "Email prepared but not sent (dry run mode)",
  "to": "test@example.com",
  "subject": "Test Email"
}
```

---

### Step 3: Create Draft Email (Manual Test)

Create a draft approval file:

```bash
cd AI_Employee_Vault

echo --- > Pending_Approval\TEST_Email_Draft.md
echo type: approval_request >> Pending_Approval\TEST_Email_Draft.md
echo action: email_create_draft >> Pending_Approval\TEST_Email_Draft.md
echo to: your-email@gmail.com >> Pending_Approval\TEST_Email_Draft.md
echo subject: Test from AI Employee >> Pending_Approval\TEST_Email_Draft.md
echo body: This is a test email draft created by the AI Employee system. >> Pending_Approval\TEST_Email_Draft.md
echo --- >> Pending_Approval\TEST_Email_Draft.md
echo >> Pending_Approval\TEST_Email_Draft.md
echo # Test Email Draft >> Pending_Approval\TEST_Email_Draft.md
echo >> Pending_Approval\TEST_Email_Draft.md
echo Move to Approved to create draft. >> Pending_Approval\TEST_Email_Draft.md
```

---

### Step 4: Approve and Execute

```bash
# Move to Approved
move Pending_Approval\TEST_Email_Draft.md Approved\

# Start orchestrator to process it
cd scripts
python approval_orchestrator.py --interval 5
```

Wait 10 seconds, then check Gmail drafts folder.

---

### Step 5: Verify Draft Created

Open Gmail in browser and check Drafts folder.

**Expected:** "Test from AI Employee" draft should exist

---

### Step 6: Stop Orchestrator

Press `Ctrl+C` to stop.

---

## ✅ Test Passed If

- [ ] Email server test returns success
- [ ] Draft email created in Gmail
- [ ] Action logged in audit logs
- [ ] No authentication errors

---

## ❌ Common Issues

### Issue: "Credentials not found"

**Solution:** Run `python gmail_watcher.py --auth` first

---

### Issue: "Token expired"

**Solution:** Delete `credentials/gmail_token.json` and re-authenticate

---

### Issue: Draft not created

**Cause:** Approval orchestrator not running or action type mismatch

**Solution:** Check orchestrator logs for errors

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Server test passes | ⬜ Pass / ⬜ Fail | |
| Draft created | ⬜ Pass / ⬜ Fail | |
| Logs written | ⬜ Pass / ⬜ Fail | |
| No auth errors | ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Once this test passes, move to: **Test 07: Gmail Watcher** (already working)

---

*Test Guide v1.0 - AI Employee System*
