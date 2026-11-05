import os

views_path = 'calls/views.py' if os.path.exists('calls/views.py') else 'CRM/calls/views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    views_code = f.read()

coaching_views = '''
@login_required
def api_coaching_analyze(request):
    """
    Sub-second Real-Time AI Objection Coaching Endpoint.
    Analyzes live speech utterances or manual objection category triggers.
    """
    import json
    from .ai_coaching import analyze_call_speech
    
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST
        
        speech_text = body.get('speech_text', '')
        category = body.get('category', '')
        result = analyze_call_speech(speech_text=speech_text, manual_category=category)
        return JsonResponse(result)
    
    return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)


@login_required
def api_coaching_quick_cards(request):
    """
    Returns full list of 1-click objection playbooks for telecaller screen.
    """
    from .ai_coaching import OBJECTION_PLAYBOOKS
    cards = []
    for code, p in OBJECTION_PLAYBOOKS.items():
        cards.append({
            'code': code,
            'category': p['category'],
            'icon': p['icon'],
            'rebuttal': p['rebuttal'],
            'talking_points': p['talking_points'],
            'action_pitch': p['action_pitch']
        })
    return JsonResponse({'success': True, 'playbooks': cards})
'''

if "def api_coaching_analyze" not in views_code:
    views_code += "\n" + coaching_views
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(views_code)
    print("ADDED_COACHING_VIEWS")
else:
    print("COACHING_VIEWS_ALREADY_PRESENT")

urls_path = 'calls/urls.py' if os.path.exists('calls/urls.py') else 'CRM/calls/urls.py'
with open(urls_path, 'r', encoding='utf-8') as f:
    urls_code = f.read()

new_routes = """    # Real-Time AI Objection Coaching Bridge (Phase 5, Item 150)
    path('calls/api/coaching/analyze/', views.api_coaching_analyze, name='api_coaching_analyze'),
    path('calls/api/coaching/quick-cards/', views.api_coaching_quick_cards, name='api_coaching_quick_cards'),
]"""

idx = urls_code.rfind(']')
if idx != -1 and "api_coaching_analyze" not in urls_code:
    urls_code = urls_code[:idx] + new_routes + urls_code[idx+1:]
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(urls_code)
    print("ADDED_COACHING_ROUTES")
else:
    print("ROUTES_ALREADY_PRESENT_OR_NOT_FOUND")
