from django.urls import path
from .views import RegisterAPI, LoginAPI, VerifyOTPAPI, LogoutAPI, UserProfileAPI, ToggleFavoriteAPI, \
    FavoriteProductsAPI

urlpatterns = [
    path('signup/', RegisterAPI.as_view(), name='signup'),
    path('signin/', LoginAPI.as_view(), name='login'),
    path('verify-otp/', VerifyOTPAPI.as_view(), name='verify_tp'),
    path('profile/', UserProfileAPI.as_view(), name='profile'),
    path('toggle-favorite/', ToggleFavoriteAPI.as_view(), name='toggle_favorite'),
    path('favorites/', FavoriteProductsAPI.as_view(), name='favorite_products'),
    path('logout/', LogoutAPI.as_view(), name='logout'),
]