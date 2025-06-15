from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, UserProfileView, ChangePasswordView,
    UserCreateView, UserListView, UserDetailView
)

# Import CSV views for teachers
from apps.students.csv_views import (
    import_teachers_csv, export_teachers_csv,
    download_teacher_csv_template, check_import_status
)

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Profile
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # User Management (for admins)
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    
    # Teacher CSV Import/Export
    path('teachers/import/csv/', import_teachers_csv, name='import_teachers_csv'),
    path('teachers/export/csv/', export_teachers_csv, name='export_teachers_csv'),
    path('teachers/template/csv/', download_teacher_csv_template, name='teacher_csv_template'),
    path('teachers/import/status/<str:task_id>/', check_import_status, name='teacher_import_status'),
]