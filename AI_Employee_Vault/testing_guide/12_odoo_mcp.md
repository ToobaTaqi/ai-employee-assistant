# Test 12: Odoo MCP Server

**Priority:** Low  
**Time Required:** 30 minutes  
**Accounts Needed:** Odoo ERP instance  

---

## ⚠️ Status: SKIP (Requires Odoo Installation)

This component requires Odoo Community Edition installed locally or on a cloud server.

**Skip this test if:**
- You don't have Odoo installed
- You're not testing accounting integration
- You're focusing on core functionality only

---

## 📋 What This Tests (If You Have Odoo)

The Odoo MCP Server provides integration with Odoo ERP for:
- Creating invoices
- Recording payments
- Managing customers/vendors
- Generating financial reports

---

## 🧪 Test Steps (If Testing)

### Step 1: Install Odoo (If Not Installed)

**Option A: Local Installation**
- Download from [odoo.com](https://odoo.com)
- Install Odoo 19+ Community Edition

**Option B: Docker**
```bash
docker run -p 8069:8069 odoo:19.0
```

---

### Step 2: Configure Odoo MCP Server

```bash
cd AI_Employee_Vault/scripts
python ..\mcp_servers\odoo_mcp_server.py --configure
```

Enter:
- Odoo URL: `http://localhost:8069`
- Database name
- Username/email
- Password

---

### Step 3: Test Connection

```bash
python ..\mcp_servers\odoo_mcp_server.py --test
```

**Expected Output:**
```json
{
  "success": true,
  "message": "Connected to Odoo",
  "financial_summary": {
    "total_revenue": 0,
    "total_expenses": 0,
    ...
  }
}
```

---

### Step 4: Test Invoice Creation

Via MCP server or create approval file:

```bash
cd AI_Employee_Vault

echo --- > Pending_Approval\TEST_Odoo_Invoice.md
echo type: approval_request >> Pending_Approval\TEST_Odoo_Invoice.md
echo action: odoo_create_invoice >> Pending_Approval\TEST_Odoo_Invoice.md
echo partner_id: 1 >> Pending_Approval\TEST_Odoo_Invoice.md
echo amount: 100 >> Pending_Approval\TEST_Odoo_Invoice.md
echo description: Test Invoice >> Pending_Approval\TEST_Odoo_Invoice.md
echo --- >> Pending_Approval\TEST_Odoo_Invoice.md
```

---

## ✅ Test Passed If (When Tested)

- [ ] Odoo connection succeeds
- [ ] Financial summary retrieved
- [ ] Invoice creation works
- [ ] Payment recording works
- [ ] Partner management works

---

## 📊 Test Results

| Check | Status | Notes |
|-------|--------|-------|
| Odoo installed | ⬜ N/A / ⬜ Pass / ⬜ Fail | |
| Connection works | ⬜ N/A / ⬜ Pass / ⬜ Fail | |
| Invoice creation | ⬜ N/A / ⬜ Pass / ⬜ Fail | |
| Payment recording | ⬜ N/A / ⬜ Pass / ⬜ Fail | |

**Overall:** ⬜ SKIP / ⬜ PASS / ⬜ FAIL

---

## ➡️ Testing Complete!

Once all applicable tests are complete, fill out the summary in `README.md`

---

*Test Guide v1.0 - AI Employee System*
