import os

views_path = 'chat/views.py' if os.path.exists('chat/views.py') else 'CRM/chat/views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    views_code = f.read()

new_classes = '''
class ConversationMetaWindowAPI(APIView):
    """
    GET /api/conversations/<id>/meta-window/
    Returns the real-time Meta 24-hour service policy window status.
    """
    def get(self, request, pk):
        conversation = _conversation_or_403(request.user, pk)
        return Response({
            'success': True,
            'meta_window': conversation.meta_window_info
        }, status=status.HTTP_200_OK)


class SendCourseKitAPI(APIView):
    """
    POST /api/conversations/<id>/send-course-kit/
    1-Click Course Kit & Syllabus PDF brochure dispatch for WhatsApp.
    """
    def post(self, request, pk):
        conversation = _conversation_or_403(request.user, pk)
        course_name = request.data.get('course_name') or request.POST.get('course_name') or 'Full Stack Development'
        
        brochure_text = (
            f"Hello {conversation.customer_name}! 🎓 Here is your official Course Kit & Curriculum Syllabus for "
            f"*{course_name}* from iTechPanda Academy.\\n\\n"
            f"📄 Complete Syllabus PDF: https://itechpanda.com/brochures/{course_name.lower().replace(' ', '-')}.pdf\\n"
            f"🕒 Next Batch: Upcoming Monday\\n"
            f"💡 100% Practical Training with Live Capstone Projects & Placement Support.\\n\\n"
            f"Reply with *1* to speak with a Counselor, or *2* to register for a Free Demo Class!"
        )

        msg = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_AGENT,
            message_type=Message.TYPE_TEXT,
            message_text=brochure_text,
            status='sent',
            sent_at=timezone.now()
        )
        conversation.last_message = f"📚 Course Kit sent ({course_name})"
        conversation.last_message_time = timezone.now()
        conversation.save(update_fields=['last_message', 'last_message_time'])

        return Response({
            'success': True,
            'message': 'Course Kit dispatched successfully via WhatsApp!',
            'message_id': msg.id,
            'course_name': course_name
        }, status=status.HTTP_200_OK)
'''

if "class ConversationMetaWindowAPI" not in views_code:
    views_code += "\n" + new_classes
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(views_code)
    print("ADDED_META_WINDOW_AND_COURSE_KIT_VIEWS")
else:
    print("VIEWS_ALREADY_PRESENT")

# Now patch chat/urls.py
urls_path = 'chat/urls.py' if os.path.exists('chat/urls.py') else 'CRM/chat/urls.py'
with open(urls_path, 'r', encoding='utf-8') as f:
    urls_code = f.read()

new_routes = """    path('api/conversations/<int:pk>/meta-window/', views.ConversationMetaWindowAPI.as_view(), name='api-conversation-meta-window'),
    path('api/conversations/<int:pk>/send-course-kit/', views.SendCourseKitAPI.as_view(), name='api-conversation-send-course-kit'),
"""

target_url = "path('api/conversations/<int:pk>/messages/', views.ConversationMessagesAPI.as_view(), name='api-conversation-messages'),"
if target_url in urls_code and "send-course-kit" not in urls_code:
    urls_code = urls_code.replace(target_url, target_url + "\n" + new_routes, 1)
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(urls_code)
    print("ADDED_CHAT_ROUTES")
else:
    print("ROUTES_ALREADY_PRESENT_OR_TARGET_NOT_FOUND")
