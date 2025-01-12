from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    # def ready(self):
    #     self.create_superuser()

    # def create_superuser(self):
    #     User = get_user_model()
    #     email = settings.SUPERUSER_EMAIL
    #     password = settings.SUPERUSER_PASSWORD

    #     if not User.objects.filter(email=email).exists():
    #         User.objects.create_superuser(email=email, password=password)
    #         print(f'Superuser "{email}" created successfully.')
    #     else:
    #         print(f'Superuser "{email}" already exists.')

