import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from Template.models import UppercaseCharField

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CreditCard(models.Model):
    card_number = models.CharField(max_length=16)
    expiration_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.cardholder_name} - {self.card_number[-4:]}'

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.BigIntegerField(null=True, blank=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    department_code = models.CharField(max_length=10, null=True, blank=True)
    employee_id = models.CharField(max_length=20, null=True, blank=True)
    currency = UppercaseCharField(max_length=5, default="USD")
    em_cc_card_id = models.CharField(max_length=80, null=True, blank=True)
    company_code = models.CharField(max_length=10, null=True, blank=True)
    set_of_books_id = models.IntegerField(null=True, blank=True)
    org_id = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    error_status = models.CharField(max_length=200, null=True, blank=True)
    integration_status = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'currency']

    class Meta:
        unique_together = ['user_id', 'email']

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if self.currency:
            self.currency = self.currency.upper()

        super().save(*args, **kwargs)

