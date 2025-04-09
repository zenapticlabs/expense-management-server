# ocr_scanner/urls.py

from django.urls import path
from .views import upload_file, scan_file

urlpatterns = [
    path('scan/', scan_file),
    path('upload/', upload_file),
]
