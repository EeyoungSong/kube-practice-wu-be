from django.urls import path
from .views import (
    SignupView, LoginView, LogoutView, TokenRefreshView,
    GoogleLoginView, GoogleCallbackView, GoogleUserInfoView, ProfileManagementView
)

app_name = 'accounts'

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileManagementView.as_view(), name='profile_management'),
    
    # Google OAuth2 URLs
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    path('google/user/', GoogleUserInfoView.as_view(), name='google_user_info'),
] 