from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from users.models import CreditCard

User = get_user_model()

class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ['card_number', 'expiration_date']

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'currency', 'department', 'password']
        extra_kwargs = {'password': {'write_only': True}}
        
    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')

        # Check if user with the same email already exists and is active
        if User.objects.filter(email=email, is_active=True).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})

        # Check if user with the same phone number already exists and is active
        if User.objects.filter(phone_number=phone_number, is_active=True).exists():
            raise serializers.ValidationError({'phone_number': 'A user with this phone number already exists.'})

        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            data['user'] = user
            return data
        raise serializers.ValidationError("Invalid login credentials")
    
class UserSerializer(serializers.ModelSerializer):
    cc_card = CreditCardSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'currency', 'department', 'cc_card', 'created_at', 'updated_at']
        read_only_fields = ['email', 'phone_number', 'created_at', 'updated_at']
