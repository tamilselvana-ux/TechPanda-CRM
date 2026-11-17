#!/usr/bin/env python3
"""
Automated CI / pre-commit check script:
Verifies that no emoji characters are present in application UI files
(HTML templates, static JavaScript/CSS, and core UI Python modules).

Allow-listed files:
- Outgoing student WhatsApp messaging templates (e.g. CRM/chat/whatsapp/ai_concierge.py)
  which are cataloged in docs/OUTGOING_MESSAGES_EMOJI_AUDIT.md and preserved.
"""

import os
import sys
import re

EMOJI_REGEX = re.compile(
    r'[\U0001F000-\U0001FAFF\u2600-\u27BF\U0001F1E6-\U0001F1FF\u2B00-\u2BFF\uFE0F\u200D]'
)

TARGET_DIRS = [
    'CRM/templates',
    'CRM/static',
    'CRM/accounts',
    'CRM/leads',
    'CRM/counselors',
    'CRM/telecallers',
    'CRM/branches',
    'CRM/chat',
    'CRM/activities',
    'CRM/calls',
    'CRM/followups',
    'CRM/fb_leads',
    'CRM/finance',
]

EXCLUDE_DIRS = {
    'venv',
    'node_modules',
    'staticfiles',
    'migrations',
    '__pycache__',
    '.git',
    '.gemini',
    'scratch',
}

# Allow-list for documented outgoing message templates
ALLOWLISTED_FILES = {
    'ai_concierge.py',  # CRM/chat/whatsapp/ai_concierge.py
}


def check_no_emoji():
    violations = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for target in TARGET_DIRS:
        full_target = os.path.join(base_dir, target)
        if not os.path.exists(full_target):
            # Check relative to current working directory
            full_target = os.path.abspath(target)
            if not os.path.exists(full_target):
                continue

        for root, dirs, files in os.walk(full_target):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if not file.endswith(('.html', '.js', '.css', '.py')):
                    continue
                if file in ALLOWLISTED_FILES:
                    continue

                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, base_dir).replace('\\', '/')

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_no, line in enumerate(f, 1):
                            matches = EMOJI_REGEX.findall(line)
                            if matches:
                                violations.append((relpath, line_no, ''.join(matches), line.strip()))
                except Exception as e:
                    print(f"Warning: could not read {relpath}: {e}", file=sys.stderr)

    if violations:
        print(f"❌ Emoji check FAILED: {len(violations)} emoji occurrence(s) found in UI files:")
        for relpath, line_no, chars, text in violations:
            print(f"  {relpath}:{line_no} [{chars}] -> {text[:80]}")
        sys.exit(1)
    else:
        print("✅ Emoji check PASSED: 0 emojis found in UI templates, static assets, and Python modules.")
        sys.exit(0)


if __name__ == '__main__':
    check_no_emoji()
