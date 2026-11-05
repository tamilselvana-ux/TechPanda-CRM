import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from chat.models import Conversation, Message, BusinessAccount
from chat.views import ConversationMetaWindowAPI, SendCourseKitAPI, InboxView
from accounts.models import UserRole

User = get_user_model()

print("--- TESTING ITEM 147: WHATSAPP 24H WINDOW & 1-CLICK COURSE KIT ---")

# 1. Setup Admin & Business Account
admin, _ = User.objects.get_or_create(
    username="admin_wa_test",
    defaults={"role": UserRole.ADMIN, "first_name": "Admin", "last_name": "User"}
)
admin.role = UserRole.ADMIN
admin.save()

biz, _ = BusinessAccount.objects.get_or_create(
    phone_number_id="100998877",
    defaults={"name": "iTechPanda Official", "phone_number": "+919876543210"}
)

now = timezone.now()

# Conversation 1: Active 24h Window (Student messaged 2 hours ago)
conv_active, _ = Conversation.objects.get_or_create(
    phone_number="+919840112233",
    defaults={"customer_name": "Deepak Raj", "business_account": biz}
)
conv_active.business_account = biz
conv_active.save()

msg_active, _ = Message.objects.get_or_create(
    conversation=conv_active,
    message_text="Hi, can you share Python syllabus?",
    sender=Message.SENDER_CUSTOMER,
    defaults={"timestamp": now - timedelta(hours=2)}
)
Message.objects.filter(id=msg_active.id).update(created_at=now - timedelta(hours=2), timestamp=now - timedelta(hours=2))

# Conversation 2: Expired 24h Window (Student messaged 30 hours ago)
conv_expired, _ = Conversation.objects.get_or_create(
    phone_number="+919840112244",
    defaults={"customer_name": "Ananya Sharma", "business_account": biz}
)
conv_expired.business_account = biz
conv_expired.save()

msg_expired, _ = Message.objects.get_or_create(
    conversation=conv_expired,
    message_text="Hello, thanks",
    sender=Message.SENDER_CUSTOMER,
    defaults={"timestamp": now - timedelta(hours=30)}
)
Message.objects.filter(id=msg_expired.id).update(created_at=now - timedelta(hours=30), timestamp=now - timedelta(hours=30))

# 2. Test Model property
win_active = conv_active.meta_window_info
assert win_active['is_active'] is True, f"Expected active window, got {win_active}"
assert win_active['requires_template'] is False
assert "24h Window Active" in win_active['text']

win_expired = conv_expired.meta_window_info
assert win_expired['is_active'] is False, f"Expected expired window, got {win_expired}"
assert win_expired['requires_template'] is True
assert "Window Expired" in win_expired['text']
print("✅ Test 1 Passed: Conversation.meta_window_info accurately calculates active vs expired window states.")

# 3. Test API Endpoint for meta-window
api_factory = APIRequestFactory()
req_win = api_factory.get(f'/api/conversations/{conv_active.id}/meta-window/')
req_win.user = admin
res_win = ConversationMetaWindowAPI.as_view()(req_win, pk=conv_active.id)
assert res_win.status_code == 200
data_win = res_win.data
assert data_win['success'] is True
assert data_win['meta_window']['is_active'] is True
print("✅ Test 2 Passed: /api/conversations/<id>/meta-window/ returned status 200 with window metrics.")

# 4. Test 1-Click Course Kit Dispatcher API
req_kit = api_factory.post(
    f'/api/conversations/{conv_active.id}/send-course-kit/',
    {'course_name': 'Full Stack Python AI'},
    format='json'
)
req_kit.user = admin
res_kit = SendCourseKitAPI.as_view()(req_kit, pk=conv_active.id)
assert res_kit.status_code == 200
data_kit = res_kit.data
assert data_kit['success'] is True
assert "dispatched successfully" in data_kit['message']

# Verify message was logged to DB
last_msg = conv_active.messages.order_by('-created_at').first()
assert "Course Kit" in last_msg.message_text
assert "Full Stack Python AI" in last_msg.message_text
assert last_msg.sender == Message.SENDER_AGENT
print("✅ Test 3 Passed: 1-Click Course Kit Dispatcher created agent message with syllabus link and updated conversation.")

# 5. Test Inbox View Rendering
factory = RequestFactory()
req_inbox = factory.get('/whatsapp/')
req_inbox.user = admin
req_inbox.session = {}
res_inbox = InboxView.as_view()(req_inbox)
assert res_inbox.status_code == 200
html_inbox = res_inbox.content.decode('utf-8')
assert "metaWindowBadge" in html_inbox, "Inbox header must contain metaWindowBadge"
assert "btnSendCourseKit" in html_inbox, "Inbox header must contain btnSendCourseKit"
print("✅ Test 4 Passed: WhatsApp Inbox HTML rendered meta window badge & course kit button with HTTP 200 OK.")

print("--- ALL TESTS PASSED FOR ITEM 147 ---")
