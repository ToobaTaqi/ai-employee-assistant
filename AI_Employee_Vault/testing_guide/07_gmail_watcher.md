# Test 07: Gmail Watcher

**Priority:** High  
**Time Required:** 15 minutes  
**Accounts Needed:** Gmail account with API access  

---

## ✅ Status: WORKING

This component has been tested and is working correctly.

---

## 📋 What This Tests

The Gmail Watcher monitors your Gmail inbox for new unread/important emails and creates action files for processing.

**Expected Behavior:**
- Monitors Gmail every 2 minutes
- Detects unread and important emails
- Creates action files in `Needs_Action/`
- Filters by priority keywords

---

## 🧪 Quick Test (If Not Already Tested)

### Step 1: Setup Gmail API (First Time Only)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop app)
5. Download `credentials.json`
6. Save to `AI_Employee_Vault/credentials/credentials.json`

### Step 2: Authenticate

```bash
cd AI_Employee_Vault/scripts
python gmail_watcher.py --auth
```

Browser will open - sign in and grant permissions.

---

### Step 3: Start Watcher

```bash
python gmail_watcher.py --interval 60
```

---

### Step 4: Send Test Email

From another email account, send an email to your Gmail:
- **Subject:** "Test - Invoice Payment Urgent"
- **Mark as Important** (star it)

---

### Step 5: Check for Action File

Wait 60 seconds, then:

```bash
dir ..\Needs_Action\EMAIL_*.md
```

**Expected:** New action file should appear

---

## ✅ Test Passed If

- [ ] Authentication succeeds
- [ ] Watcher starts without errors
- [ ] Action file created for test email
- [ ] Email content extracted correctly
- [ ] Priority keywords detected

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Authentication works | ✅ Pass | Already tested |
| Watcher starts | ✅ Pass | Already tested |
| Detects emails | ✅ Pass | Already tested |
| Creates action files | ✅ Pass | Already tested |

**Overall:** ✅ PASS

---

## ➡️ Next Test

Move to: **Test 08: WhatsApp Watcher** (partially working)

---

*Test Guide v1.0 - AI Employee System*
