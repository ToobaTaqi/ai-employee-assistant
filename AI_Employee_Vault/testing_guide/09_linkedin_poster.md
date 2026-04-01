# Test 09: LinkedIn Auto-Poster

**Priority:** Medium  
**Time Required:** 15 minutes  
**Accounts Needed:** LinkedIn account (for posting)  

---

## ✅ Status: WORKING

**What Works:**
- ✅ Generate LinkedIn content
- ✅ Create draft posts
- ✅ Schedule posts
- ✅ **Auto-post to LinkedIn** (opens browser, requires login)
- ✅ HITL approval workflow

---

## 🧪 Test Steps

### Step 1: Generate Content (Optional)

```bash
cd AI_Employee_Vault/scripts
python linkedin_poster.py --generate --topic "AI Trends" --tone professional
```

---

### Step 2: Create Draft Post

```bash
python linkedin_poster.py --draft "Excited to share our AI Employee system! Automating business tasks with AI. #AI #Automation #Innovation"
```

**Expected:**
```
✓ Draft created: ...\Social_Media\LinkedIn\Drafts\LinkedIn_Draft_20260401_XXXXXX.md
```

---

### Step 3: Post to LinkedIn (Automatic)

```bash
python linkedin_poster.py --post-auto
```

**What happens:**
1. Browser opens
2. If not logged in, you have 60 seconds to log in
3. Script navigates to feed
4. Clicks "Start a post"
5. Types your content
6. Clicks "Post"
7. Moves file to Published/ folder

**Expected:**
```
Posting to LinkedIn:
Excited to share our AI Employee system!...

⚠️  You need to log in to LinkedIn first!
   Please log in manually...

✓ Login detected!

✓ Post published to LinkedIn!
✓ Post published! File moved to: ...\Published\LinkedIn_Draft_...md
```

---

### Step 4: Verify Post

1. Check your LinkedIn feed - post should be visible
2. Check Published folder:
   ```bash
   dir ..\Social_Media\LinkedIn\Published\
   ```

---

## ✅ Test Passed If

- [ ] Content generation works
- [ ] Draft created in Drafts/
- [ ] Auto-post opens browser
- [ ] Can log in and post
- [ ] Post appears on LinkedIn
- [ ] File moved to Published/

---

## ❌ Common Issues

### Issue: "Not logged in" timeout

**Solution:** Log in faster (within 60 seconds) or run again - session will be saved

### Issue: Post button not found

**Cause:** LinkedIn UI changed

**Solution:** Manual posting - copy draft content and paste on LinkedIn

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Content generation | ⬜ Pass / ⬜ Fail | |
| Draft creation | ⬜ Pass / ⬜ Fail | |
| Auto-post works | ⬜ Pass / ⬜ Fail | |
| Post on LinkedIn | ⬜ Pass / ⬜ Fail | |
| File moved to Published | ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ PASS / ⬜ FAIL

---

## ➡️ Next Test

Move to: **Test 10: Ralph Wiggum Loop**

---

*Test Guide v1.0 - AI Employee System*
