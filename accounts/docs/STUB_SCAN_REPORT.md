# Stub & Incomplete-Code Scan

Run: 2026-11-16 23:16 · Root: `D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\accounts`

**Blockers:** 0 · **Warnings:** 2 · **Verdict:** ✅ no stubs found

## 🚫 Blockers (must fix before 'done')
| Rule | File | Line | Code |
|---|---|---|---|
| — | — | — | none |

## ⚠️ Warnings (review)
| Rule | File | Line | Code |
|---|---|---|---|
| Hard-coded localhost URL | services.py | 133 | `base_url = getattr(settings, 'CRM_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')` |
| Hard-coded localhost URL | services.py | 286 | `base_url = getattr(settings, 'CRM_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')` |

