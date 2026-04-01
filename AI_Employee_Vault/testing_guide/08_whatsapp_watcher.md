# Test 08: WhatsApp Watcher

**Priority:** High  
**Time Required:** 15 minutes  
**Accounts Needed:** WhatsApp account  

---

## ⚠️ Status: PARTIALLY WORKING

**What Works:**
- ✅ Detects unread chats
- ✅ Extracts message previews
- ✅ Filters by priority keywords
- ✅ Creates action files

**Known Issue:**
- ⚠️ Browser fails to restart after first cycle on Windows (Playwright persistent context issue)

**Workaround:** Use longer check intervals (60+ seconds) or restart manually between cycles.

---

## 🧪 Quick Test

### Step 1: Start WhatsApp Watcher

```bash
cd AI_Employee_Vault/scripts
python whatsapp_watcher.py --visible --interval 60
```

**First Run:** Browser will open - scan QR code with WhatsApp mobile app:
1. Open WhatsApp on phone
2. Settings → Linked Devices
3. Link a Device
4. Scan QR code

---

### Step 2: Send Test Message

Send yourself a WhatsApp message with priority keywords:
- **Message:** "Hey, please send me the invoice urgently"

---

### Step 3: Wait for Detection

Wait 60 seconds (one check cycle).

---

### Step 4: Check for Action File

```bash
dir ..\Needs_Action\WHATSAPP_*.md
```

**Expected:** New action file should appear

---

### Step 5: Inspect Action File

```bash
type ..\Needs_Action\WHATSAPP_*.md
```

**Expected Content:**
```markdown
---
type: whatsapp
chat_name: [Your Name]
priority: high
---

# WhatsApp Message Received

## Message Content
Hey, please send me the invoice urgently

## Suggested Actions
- [ ] Extract payment details
- [ ] Create approval request
...
```

---

## ✅ Test Passed If

- [ ] QR code scan succeeds
- [ ] Watcher detects unread message
- [ ] Action file created
- [ ] Message content extracted correctly
- [ ] Priority keywords detected ("invoice", "urgently")

---

## ❌ Known Issue: Browser Restart Fails

### Symptom
```
ERROR - Failed to initialize browser: BrowserType.launch_persistent_context: Target page, context or browser has been closed
```

### Workaround

**Option 1: Increase Interval**
```bash
python whatsapp_watcher.py --interval 120  # Check every 2 minutes
```

**Option 2: Manual Restart**
1. Stop with Ctrl+C
2. Wait 5 seconds
3. Restart: `python whatsapp_watcher.py --visible`

**Option 3: Use PM2 (Recommended for Production)**
```bash
npm install -g pm2
pm2 start whatsapp_watcher.py --name "whatsapp" --interpreter python3 -- --interval 60
```

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| QR authentication | ⬜ Pass / ⬜ Fail | |
| Detects unread chats | ⬜ Pass / ⬜ Fail | |
| Extracts messages | ⬜ Pass / ⬜ Fail | |
| Creates action files | ⬜ Pass / ⬜ Fail | |
| Browser stays connected | ⬜ Pass / ⬜ Fail | Known issue |

**Overall:** ⬜ PASS (with workaround) / ⬜ FAIL

---

## ➡️ Next Test

Move to: **Test 09: LinkedIn Auto-Poster**

---

*Test Guide v1.0 - AI Employee System*
