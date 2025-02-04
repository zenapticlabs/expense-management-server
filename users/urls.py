from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import AddCreditCardView, LoginView, LogoutView, RegisterView, ResetPasswordView, UserDetailView, VerifyCodeView, VerifyRegistrationCodeView

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('verify-registration', VerifyRegistrationCodeView.as_view(), name='verify_registration'),
    path('login', LoginView.as_view(), name='login'),
    path('verify-mfa', VerifyCodeView.as_view(), name='verify_mfa'),
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('me', UserDetailView.as_view(), name='me'),
    path('credit-card', AddCreditCardView.as_view(), name='add-credit-card'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
]
