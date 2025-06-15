from django.urls import path
from .views import (
    SchoolListView, SchoolDetailView, SchoolDashboardView,
    SMTPSettingsView, SMTPSettingsCreateView,
    SchoolGroupListView, SchoolGroupDetailView,
    get_user_dashboard
)

urlpatterns = [
    # Dashboard
    path('dashboard/', get_user_dashboard, name='user_dashboard'),
    
    # Schools
    path('', SchoolListView.as_view(), name='school_list'),
    path('<int:pk>/', SchoolDetailView.as_view(), name='school_detail'),
    path('<int:pk>/dashboard/', SchoolDashboardView.as_view(), name='school_dashboard'),
    
    # SMTP Settings
    path('<int:school_id>/smtp/', SMTPSettingsView.as_view(), name='smtp_settings'),
    path('<int:school_id>/smtp/create/', SMTPSettingsCreateView.as_view(), name='smtp_create'),
    
    # School Groups
    path('groups/', SchoolGroupListView.as_view(), name='school_group_list'),
    path('groups/<int:pk>/', SchoolGroupDetailView.as_view(), name='school_group_detail'),
]