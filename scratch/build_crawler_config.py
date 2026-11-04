import json

with open('docs/role_sessions.json', 'r') as f:
    sessions = json.load(f)

cfg = {
  "baseUrl": "http://127.0.0.1:8000",
  "allowDestructive": False,
  "skipText": ["logout", "log out", "sign out", "delete", "remove", "deactivate", "cancel subscription", "pay now"],
  "maxPages": 250,
  "maxElementsPerPage": 150,
  "clickTimeoutMs": 4000,
  "settleMs": 700,
  "output": "docs/07_CLICK_TEST_REPORT",
  "headless": True,
  "viewport": { "width": 1366, "height": 850 },
  "roles": [
    {
      "name": "guest",
      "seedRoutes": ["/login/"]
    },
    {
      "name": "admin",
      "sessionCookie": sessions['admin']['sessionid'],
      "seedRoutes": [
        "/admin/dashboard/",
        "/admin/leads/",
        "/admin/leads/new/",
        "/leads/",
        "/leads/kanban/",
        "/enrollments/",
        "/accountant/verification/",
        "/admin/email-logs/",
        "/admin/calls/",
        "/calls/recordings/",
        "/admin/followups/",
        "/reports/",
        "/reports/dashboard-report/",
        "/reports/telecaller-rnr/",
        "/finance/dashboard/",
        "/accounts/users/",
        "/enrollments/receipt/63/"
      ]
    },
    {
      "name": "accountant",
      "sessionCookie": sessions['accountant']['sessionid'],
      "seedRoutes": [
        "/accountant/dashboard/",
        "/accountant/verification/",
        "/enrollments/",
        "/finance/dashboard/"
      ]
    },
    {
      "name": "counselor",
      "sessionCookie": sessions['counselor']['sessionid'],
      "seedRoutes": [
        "/counselor/dashboard/",
        "/counselor/workspace/",
        "/counselor/leads/",
        "/counselor/followups/",
        "/enrollments/"
      ]
    },
    {
      "name": "telecaller",
      "sessionCookie": sessions['telecaller']['sessionid'],
      "seedRoutes": [
        "/telecaller/dashboard/",
        "/telecaller/workspace/",
        "/telecaller/calls/",
        "/telecaller/leads/"
      ]
    },
    {
      "name": "branch_head",
      "sessionCookie": sessions['branch_head']['sessionid'],
      "seedRoutes": [
        "/manager/branch-head/dashboard/",
        "/branch-head/dashboard/",
        "/branch-head/leads/"
      ]
    },
    {
      "name": "sales_head",
      "sessionCookie": sessions['sales_head']['sessionid'],
      "seedRoutes": [
        "/manager/dashboard/",
        "/manager/leads/",
        "/manager/calls/",
        "/manager/followups/"
      ]
    },
    {
      "name": "receptionist",
      "sessionCookie": sessions['receptionist']['sessionid'],
      "seedRoutes": [
        "/receptionist/dashboard/",
        "/receptionist/walkin/",
        "/receptionist/visitors/"
      ]
    }
  ]
}

with open('docs/crawler.config.json', 'w') as f:
    json.dump(cfg, f, indent=2)

print("Generated docs/crawler.config.json with 8 roles successfully!")
