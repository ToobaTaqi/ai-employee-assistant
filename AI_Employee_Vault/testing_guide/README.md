# AI Employee Testing Guide

## 📋 Overview

This folder contains step-by-step testing guides for each component of the AI Employee system.

**Total Components:** 12  
**Estimated Testing Time:** 2-3 hours  
**Difficulty:** Beginner to Intermediate

---

## 🎯 Testing Order

### Phase 1: Core Components (No Accounts Required)
Test these first - they don't need any external accounts.

| # | Component | File | Time | Status |
|---|-----------|------|------|--------|
| 1 | **Plan Generator** | `01_plan_generator.md` | 10 min | ⏳ Not tested |
| 2 | **Dashboard Updater** | `02_dashboard_updater.md` | 5 min | ⏳ Not tested |
| 3 | **Briefing Generator** | `03_briefing_generator.md` | 10 min | ⏳ Not tested |
| 4 | **Task Scheduler** | `04_task_scheduler.md` | 10 min | ⏳ Not tested |
| 5 | **Approval Orchestrator** | `05_approval_orchestrator.md` | 15 min | ⏳ Not tested |

### Phase 2: Email Integration (Gmail Account Required)
Requires Gmail API setup.

| # | Component | File | Time | Status |
|---|-----------|------|------|--------|
| 6 | **Email MCP Server** | `06_email_mcp_server.md` | 20 min | ⏳ Not tested |
| 7 | **Gmail Watcher** | `07_gmail_watcher.md` | 15 min | ✅ Working |

### Phase 3: Social Media (Optional Accounts)
Requires social media accounts.

| # | Component | File | Time | Status |
|---|-----------|------|------|--------|
| 8 | **WhatsApp Watcher** | `08_whatsapp_watcher.md` | 15 min | ⚠️ Partial |
| 9 | **LinkedIn Auto-Poster** | `09_linkedin_poster.md` | 15 min | ⏳ Not tested |

### Phase 4: Advanced Features
Gold/Platinum tier features.

| # | Component | File | Time | Status |
|---|-----------|------|------|--------|
| 10 | **Ralph Wiggum Loop** | `10_ralph_wiggum.md` | 15 min | ⏳ Not tested |
| 11 | **Error Recovery System** | `11_error_recovery.md` | 10 min | ⏳ Not tested |
| 12 | **Odoo MCP Server** | `12_odoo_mcp.md` | 30 min | ⏳ Skip (needs Odoo) |

---

## ✅ How to Use

1. **Start with Phase 1** - No accounts needed
2. **Mark each test as complete** - Check the Status column
3. **Report issues** - Note any errors in the test file
4. **Move to next phase** - Only after all tests pass

---

## 📊 Test Results Summary

| Phase | Total Tests | Passed | Failed | Skipped |
|-------|-------------|--------|--------|---------|
| Phase 1 | 5 | 0 | 0 | 5 |
| Phase 2 | 2 | 1 | 0 | 1 |
| Phase 3 | 2 | 0 | 0 | 2 |
| Phase 4 | 3 | 0 | 0 | 3 |
| **TOTAL** | **12** | **1** | **0** | **11** |

---

## 🐛 Known Issues

| Component | Issue | Status |
|-----------|-------|--------|
| WhatsApp Watcher | Browser restart fails on Windows | ⚠️ Workaround available |
| Plan Generator | Filename generation bug | ✅ Fixed |

---

## 📞 Need Help?

If a test fails:
1. Check the error message
2. Review the troubleshooting section
3. Check logs in `AI_Employee_Vault/logs/`
4. Ask for help with the error details

---

*Last Updated: March 30, 2026*  
*AI Employee System v1.0 - Silver + Gold Tier*
