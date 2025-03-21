from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate

from users.models import User
from users.permissioins import HasResetClaim, PasswordResetRequestAuthentication
from users.utils import send_password_reset_email
from .serializers import CreditCardSerializer, PasswordResetConfirmSerializer, LoginSerializer, ResetPasswordSerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class AddCreditCardView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.cc_card

    def post(self, request, *args, **kwargs):
        if request.user.cc_card:
            return Response({'detail': 'User already has a credit card'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credit_card = serializer.save()
        request.user.cc_card = credit_card
        request.user.save()

        return Response({'detail': 'Credit card added successfully', 'credit_card': serializer.data}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)
        validated_data = serializer.validated_data
        user = validated_data['user']

        if user is None:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    

class ResetPasswordView(generics.UpdateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password updated successfully."})
    

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(generics.GenericAPIView):
    authentication_classes = [PasswordResetRequestAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        send_password_reset_email(email)

        return Response({'message': 'Password reset email has been sent.'}, status=status.HTTP_200_OK)
    

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmView(generics.GenericAPIView):
    authentication_classes = [PasswordResetRequestAuthentication]
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny, HasResetClaim]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data.get('new_password')
        try:
            user = User.objects.get(id=request.user_id_from_token)
        except Exception:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.is_active:
            user.is_active = True
            user.save()

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)

