from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponsePermanentRedirect

import fb_leads.views
from accounts import views_public
from config.sitemaps import sitemaps


def redirect_facebook_to_meta(request, subpath=""):
    sub = (subpath or "").lstrip("/")
    target = f"/meta-leads/{sub}" if sub else "/meta-leads/"
    if not target.endswith("/"):
        target += "/"
    qs = request.META.get("QUERY_STRING", "")
    if qs:
        target += f"?{qs}"
    return HttpResponsePermanentRedirect(target)


urlpatterns = [
    # Public SEO-Optimized Root Landing Page
    path('', views_public.landing_page_view, name='root'),

    # Search Engine Directives & Sitemap
    path('robots.txt', views_public.robots_txt_view, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # Django Admin Site
    path('django-admin/', admin.site.urls),

    # Application Modules
    path('', include('accounts.urls')),
    path('', include('reports.urls')),
    path('', include('managers.urls')),
    path('', include('branch_heads.urls')),
    path('', include('counselors.urls')),
    path('', include('telecallers.urls')),
    path('', include('leads.urls')),
    path('', include('lead_channels.urls')),
    path('', include('products.urls')),
    path('', include('branches.urls')),
    path('', include('calls.urls')),
    path('', include('followups.urls')),
    path('', include('activities.urls')),
    path('drive/', include('drive.urls')),
    path('call-recordings/', include('drive.urls')),
    # WhatsApp inbox (/whatsapp/), automations (/automations/), WhatsApp webhook (/webhook/whatsapp/)
    path('', include('chat.urls')),
    path('chat/', include('chat.urls')),
    # Meta Lead Ads: list + sync (/meta-leads/), webhook (/meta-leads/webhook/)
    path('meta-leads/', include('fb_leads.urls')),
    path('facebook-leads/webhook/', fb_leads.views.webhook),
    re_path(r'^facebook-leads/(?P<subpath>.*)$', redirect_facebook_to_meta),
    # TeleCRM Import & Live Sync Administration Portal
    path('admin/telecrm-sync/', include('telecrm_sync.urls')),
    # Dedicated Finance Portal Suite
    path('finance/', include('finance.urls')),
    # Superadmin Local CRM Assistant (Zero-AI, Zero-API)
    path('admin/superadmin-bot/', include('superadmin_bot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
