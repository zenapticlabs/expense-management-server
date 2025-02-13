from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta

from users.models import User
from users.utils import check_verification_code, send_verification_code
from .serializers import CreditCardSerializer, RegisterSerializer, LoginSerializer, ResetPasswordSerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken

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

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')

        User.objects.filter(email=email, is_active=False).delete()
        User.objects.filter(phone_number=phone_number, is_active=False).delete()

        if User.objects.filter(email=email, is_active=True).exists():
            return Response({'email': 'A user with this email already exists.'}, status=status.HTTP_409_CONFLICT)
        if User.objects.filter(phone_number=phone_number, is_active=True).exists():
            return Response({'phone_number': 'A user with this phone number already exists.'}, status=status.HTTP_409_CONFLICT)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.perform_create(serializer)

    def perform_create(self, serializer):
        user = serializer.save()
        user.is_active = False
        
        if settings.DISABLE_MFA:
            user.is_active = True
            response = {'detail': 'User Created'}
        else:
            send_verification_code(user.phone_number.as_e164)
            response = {'detail': 'Two-factor authentication required'}
        user.save()

        return Response(response, status=status.HTTP_201_CREATED)

class VerifyRegistrationCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        code = request.data.get('code')
        try:
            user = User.objects.get(email=email)
            if check_verification_code(user.phone_number.as_e164, code):
                user.verification_code = None
                user.is_active = True
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)

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

        if user.phone_number and self.is_2fa_required(user):
            send_verification_code(user.phone_number.as_e164)
            return Response(
                {
                    'error': 'Two-factor authentication required',
                    'code': 'second_factor_required',
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        
    def is_2fa_required(self, user):
        if not hasattr(user, 'last_2fa_time') or not user.last_2fa_time or (timezone.now() - user.last_2fa_time) > timedelta(days=1):
            return True
        return False

class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        code = request.data.get('code')
        try:
            user = User.objects.get(email=email)
            if check_verification_code(user.phone_number.as_e164, code):
                if hasattr(user, 'last_2fa_time'):
                    user.last_2fa_time = timezone.now()
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid or expired verification code'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)

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

