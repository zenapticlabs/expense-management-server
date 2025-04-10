from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.conf import settings
import boto3
import os

from .utils import process_receipt

@csrf_exempt
def scan_file(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    file_key = request.POST.get('filePath')  # S3 object key
    if not file_key:
        return JsonResponse({'error': 'Missing filePath parameter'}, status=400)

    # Setup paths
    save_dir = os.path.join(settings.BASE_DIR, 'temp_receipts')
    os.makedirs(save_dir, exist_ok=True)
    local_file_path = os.path.join(save_dir, os.path.basename(file_key))

    try:
        # Create a boto3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        # Download the file from S3
        s3.download_file(settings.AWS_S3_BUCKET_NAME, file_key, local_file_path)

        # Process the file
        result = process_receipt(local_file_path)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    finally:
        # Always remove the file after processing or on error
        if os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except Exception as cleanup_err:
                # Optional: log this error
                print(f"Cleanup error: {cleanup_err}")

                

@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        save_dir = os.path.join(settings.BASE_DIR, 'uploaded_files')
        os.makedirs(save_dir, exist_ok=True)

        fs = FileSystemStorage(location=save_dir)
        filename = fs.save(uploaded_file.name, uploaded_file)
        full_path = os.path.join(save_dir, filename)

        result = process_receipt(full_path)
        return JsonResponse(result)

    return JsonResponse({'error': 'No file uploaded'}, status=400)
