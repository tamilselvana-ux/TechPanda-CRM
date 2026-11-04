# 🛡️ RULES OF ENGAGEMENT (ROE) & STRIDE THREAT MODEL
**Engagement:** Defensive Security Audit & Penetration Test — DigiPanda CRM  
**Date:** October 31, 2026  
**Lead Authority:** 👑 Founder Authorization  
**Division:** White Hat Security & Ethical Hacking Division (15 Lead + 15a–15g)  
**Standard:** OWASP Top 10 (Web & API), OWASP WSTG, CWE, India DPDP Act / GDPR data protection  

---

## 1. Scope & Authorized Boundaries

| Parameter | Specification |
| :--- | :--- |
| **Target Application** | DigiPanda CRM (Django 5.1.x, MySQL 8.0, Python 3.12, IIS/Development) |
| **Target URL / Environment**| `http://127.0.0.1:8000/` (Local / Staging Test Environment Only) |
| **Database** | Local development/staging schema (`crm_integrated_v2`) with test leads & dummy accounts |
| **Production Boundary** | **OFF-LIMITS:** Never execute attacks or intrusive tests against live production databases, real user phone numbers, or real email/SMS gateways. |
| **Testing Methodology** | **White-Box Penetration Test**: Direct source code review, architecture analysis, endpoint permission validation, dynamic test requests with safe assertion markers. |
| **Destructive Actions** | **STRICTLY PROHIBITED:** Zero denial-of-service (DoS) stress testing, zero irreversible data destruction, zero real financial transactions. |

---

## 2. Tested Roles & Trust Boundaries

The CRM operates under a multi-tier role-based access control (RBAC) model across 7 distinct user personas:
1. **Superadmin / Admin (`ADMIN`)**: Unrestricted administrative oversight across all branches, users, settings, and financial records.
2. **Sales Head (`SALES_HEAD`)**: Branch management, lead allocation, team oversight, report viewing.
3. **Branch Head (`BRANCH_HEAD`)**: Scoped to assigned physical branch; manages branch staff, leads, and counselors.
4. **Counselor (`COUNSELOR`)**: Student walk-ins, course counseling, student enrollment, fee collection, installments.
5. **Telecaller (`TELECALLER`)**: Inbound/outbound call logging, qualification, notes, lead follow-up. *Explicitly forbidden from enrolling students or finalizing fees.*
6. **Accountant (`ACCOUNTANT`)**: Financial verification queue, receipt auditing, bank reconciliation, GST verification.
7. **Receptionist (`RECEPTIONIST`)**: Walk-in visitor management, token dispatch, initial intake.

---

## 3. STRIDE Threat Model

```
+---------------------------------------------------------------------------------------+
|                                    STRIDE THREAT MATRIX                               |
+-------------------+---------------------------------------------+---------------------+
| Threat Category   | Potential Vector in DigiPanda CRM          | Target Boundary     |
+-------------------+---------------------------------------------+---------------------+
| Spoofing          | • Session hijacking via cookie manipulation | Auth & Sessions     |
|                   | • Unauthenticated fake lead intake spoofing | Ingestion Endpoints |
+-------------------+---------------------------------------------+---------------------+
| Tampering         | • Altering course fees or GST treatment     | Enrollment & Fee    |
|                   | • Unauthorized modification of student notes| Lead Detail Views   |
|                   | • Parameter tampering on split installments | Financial Engine    |
+-------------------+---------------------------------------------+---------------------+
| Repudiation       | • Action performed without audit logging    | Activity & Dupe Log |
|                   | • Unlogged status or assignment change      | Status History      |
+-------------------+---------------------------------------------+---------------------+
| Information       | • PII data leakage in API JSON responses    | REST & AJAX APIs    |
| Disclosure        | • Unmasked student phone/email exposure     | Listing & Modals    |
|                   | • Sensitive stack trace leaks (DEBUG=True)  | Error Handlers      |
+-------------------+---------------------------------------------+---------------------+
| Denial of Service | • Unthrottled API endpoint abuse            | Public Intake APIs  |
|                   | • High-cardinality regex / ReDoS            | Phone Normalizer    |
+-------------------+---------------------------------------------+---------------------+
| Elevation of      | • Horizontal IDOR: Staff viewing leads from | Lead Detail Views   |
| Privilege         |   unauthorized branches                     |                     |
|                   | • Vertical Escalation: Telecaller enrolling | Lead Status Service |
|                   |   students or changing restricted fields    |                     |
+-------------------+---------------------------------------------+---------------------+
```

---

## 4. Assessment Checklist & Division Assignments

- **15a (Web Application Pentest)**: XSS in rich fields/notes, SQLi in custom raw queries, CSRF on AJAX/POST actions, Clickjacking headers.
- **15b (API Security)**: Mass assignment in inline edit `/api/leads/inline-save/`, PII overexposure in search/duplicate endpoints, rate limits.
- **15c (Network & Infra)**: Secret key exposure, session cookie attributes (`HttpOnly`, `SameSite`, `Secure`), dependency audit (`pip-audit`).
- **15e (Auth & Access Control)**: Password strength, session invalidation on logout, IDOR on `/leads/<pk>/`, cross-branch lead snooping.
- **15f (Business Logic)**: Fee manipulation (negative values, GST bypass), unauthorized terminal status transitions, installment schedule bypass.
- **15g (Validation Specialist)**: Verify each discovered finding with safe automated test assertions and validate remediation patches.
