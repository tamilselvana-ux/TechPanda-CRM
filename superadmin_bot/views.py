import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from accounts.models import UserRole
from .engine import process_superadmin_query


@login_required
@require_POST
def superadmin_bot_ask(request):
    """
    Superadmin CRM Assistant API Endpoint.
    Strictly isolated to Superadmins only (is_superuser or role == SUPERADMIN).
    All other roles receive 403 Forbidden.
    """
    user = request.user
    if not (user.is_superuser or user.role == UserRole.SUPERADMIN):
        return JsonResponse({
            'success': False,
            'error': 'Access denied. The CRM Assistant is strictly reserved for Superadmins.'
        }, status=403)

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST

        query = payload.get('query', '').strip()
    except Exception:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request payload.'
        }, status=400)

    if not query:
        return JsonResponse({
            'success': False,
            'error': 'Please enter a valid question or command.'
        }, status=400)

    # Process query deterministically (0 external APIs)
    result = process_superadmin_query(user, query)

    return JsonResponse({
        'success': True,
        'query': query,
        'response': result
    })
