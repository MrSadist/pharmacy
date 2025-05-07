from django.urls import path
from .views import RegisterAPI, LoginAPI, VerifyOTPAPI, LogoutAPI, UserProfileAPI, ToggleFavoriteAPI, SpecialistListAPI, \
    AdminUserListAPI, AdminUserCreateAPI, AdminUserDetailAPI, AdminUserDeleteAPI

urlpatterns = [
    path('signup/', RegisterAPI.as_view(), name='signup'),
    path('signin/', LoginAPI.as_view(), name='login'),
    path('verify-otp/', VerifyOTPAPI.as_view(), name='verify_tp'),
    path('profile/', UserProfileAPI.as_view(), name='profile'),
    path('toggle-favorite/', ToggleFavoriteAPI.as_view(), name='toggle_favorite'),
    path('logout/', LogoutAPI.as_view(), name='logout'),
    path('specialists/', SpecialistListAPI.as_view(), name='specialist-list'),
    path('admin/users/', AdminUserListAPI.as_view(), name='admin-user-list'),
    path('admin/users/create/', AdminUserCreateAPI.as_view(), name='admin-user-create'),
    path('admin/users/<int:id>/', AdminUserDetailAPI.as_view(), name='admin-user-detail'),
    path('admin/users/<int:id>/delete/', AdminUserDeleteAPI.as_view(), name='admin-user-delete'),
]