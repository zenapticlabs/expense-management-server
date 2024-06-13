from django.urls import path, include

from users.views import LoginView, LogoutView, RegisterView, UserDetailView, VerifyCodeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-mfa/', VerifyCodeView.as_view(), name='verify_mfa'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', UserDetailView.as_view(), name='me')
]
