from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import AddCreditCardView, LoginView, LogoutView, PasswordResetRequestView, PasswordResetConfirmView, ResetPasswordView, UserDetailView

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('me', UserDetailView.as_view(), name='me'),
    path('credit-card', AddCreditCardView.as_view(), name='add-credit-card'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    path('forgot-password', PasswordResetRequestView.as_view(), name='forgot-password'),
    path('password-reset', PasswordResetConfirmView.as_view(), name='password-reset'),
]
