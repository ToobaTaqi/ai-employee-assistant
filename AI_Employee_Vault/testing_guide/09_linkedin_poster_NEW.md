# Test 09: LinkedIn Auto-Poster

**Priority:** Low  
**Time Required:** 10 minutes  
**Accounts Needed:** None for draft creation  

---

## ✅ Status: WORKING

**What Works:**
- ✅ Generate LinkedIn content
- ✅ Create draft posts
- ✅ Schedule posts
- ✅ HITL approval workflow

**How It Works:**
The LinkedIn poster creates drafts that require human approval before posting. This follows the HITL (Human-in-the-Loop) pattern.

**To Post:**
1. Create draft with `--draft`
2. Review the draft file
3. Post manually on LinkedIn OR move to Approved/ for automated posting

---

## 🧪 Test Steps

### Step 1: Generate Content

```bash
cd AI_Employee_Vault/scripts
python linkedin_poster.py --generate --topic "AI Trends" --tone professional
```

**Expected Output:**
```
Generated Content:

Business Update: AI Trends

We're pleased to share insights on AI Trends.
...
```

---

### Step 2: Create Draft Post

```bash
python linkedin_poster.py --draft "Testing AI Employee LinkedIn integration! #automation"
```

**Expected Output:**
```
✓ Draft created: ...\Social_Media\LinkedIn\Drafts\LinkedIn_Draft_20260401_XXXXXX.md

Next steps:
  1. Review: [path]
  2. Edit if needed
  3. Move to Approved/ when ready to post
```

---

### Step 3: Verify Draft Created

```bash
cd ..
dir Social_Media\LinkedIn\Drafts\
type Social_Media\LinkedIn\Drafts\LinkedIn_Draft_*.md
```

---

## ✅ Test Passed If

- [ ] Content generation works
- [ ] Draft files created in Drafts/
- [ ] Draft has valid markdown structure

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Content generation | ⬜ Pass / ⬜ Fail | |
| Draft creation | ⬜ Pass / ⬜ Fail | |
| Draft structure valid | ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Move to: **Test 10: Ralph Wiggum Loop**

---

*Test Guide v1.0 - AI Employee System*
