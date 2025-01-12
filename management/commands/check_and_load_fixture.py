import json
import os
from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = "Check if data exists, load fixtures, and create a superuser."

    def add_arguments(self, parser):
        parser.add_argument(
            "fixture_file",
            type=str,
            help="Relative path to the fixture file (e.g., 'fixtures/initial_data.json')",
        )

    def handle(self, *args, **options):
        fixture_file_path = options["fixture_file"]
        fixture_path = os.path.join(settings.BASE_DIR, fixture_file_path)
        
        # Create superuser
        self.create_superuser()

        # Load the fixture file
        try:
            with open(fixture_path, "r") as file:
                fixture_data = json.load(file)
        except FileNotFoundError:
            print(f"[ERROR] Fixture file not found: {fixture_path}")
            return

        # Process each entry in the fixture
        for entry in fixture_data:
            model_name = entry["model"]
            pk = entry["pk"]
            fields = entry["fields"]

            try:
                # Get the model class
                model = apps.get_model(model_name)
            except LookupError:
                print(f"[WARNING] Model {model_name} not found. Skipping.")
                continue

            try:
                # Check if the object exists
                obj = model.objects.get(pk=pk)
                print(f"[INFO] Object with PK {pk} already exists in {model_name}: {obj}")
            except ObjectDoesNotExist:
                # Create the object if it doesn't exist
                obj = model(pk=pk, **fields)
                obj.save()
                print(f"[SUCCESS] Created new object in {model_name}: {fields}")

    def create_superuser(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        email = settings.SUPERUSER_EMAIL
        password = settings.SUPERUSER_PASSWORD

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password)
            print(f"[SUCCESS] Superuser '{email}' created successfully.")
        else:
            print(f"[INFO] Superuser '{email}' already exists.")
