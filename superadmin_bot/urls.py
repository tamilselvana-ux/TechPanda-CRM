from django.urls import path
from . import views

urlpatterns = [
    path('ask/', views.superadmin_bot_ask, name='superadmin_bot_ask'),
]
