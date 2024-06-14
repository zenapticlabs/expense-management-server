import random
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate

from users.models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from twilio.rest import Client

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    # def post(self, request, *args, **kwargs):
    #     serializer = self.serializer_class(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     user = serializer.validated_data
    #     refresh = RefreshToken.for_user(user)
    #     return Response({
    #         'refresh': str(refresh),
    #         'access': str(refresh.access_token),
    #     }, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # email = serializer.validated_data['email']
        # password = serializer.validated_data['password']
        # user = authenticate(email=email, password=password)
        validated_data = serializer.validated_data
        user = validated_data['user']

        if user is None:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

        # sms_code = random.randint(100000, 999999)
        # user.sms_code = sms_code
        # user.save()
        
        user.generate_verification_code()

        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # call = client.calls.create(
        #     twiml=f'<Response><Say>Your verification code is {' '.join(user.verification_code)}</Say></Response>',
        #     to=user.phone_number.as_e164,
        #     from_=settings.TWILIO_PHONE_NUMBER
        # )

        return Response(
            {
                'error': 'Voice verification required',
                'code': 'second_factor_required',
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
        
class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        code = request.data.get('code')
        try:
            user = User.objects.get(email=email)
            if user.verify_code(code):
                user.verification_code = None  # Clear the code after successful verification
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
        
class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

