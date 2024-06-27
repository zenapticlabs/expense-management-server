import logging
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from expense_management_server import settings
from expenses.utils import delete_s3_file, generate_presigned_url
from .models import ExpenseItem, ExpenseReport
from .serializers import ExpenseItemSerializer

logger = logging.getLogger(__name__)

class ExpenseItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        report_id = self.kwargs['report_id']
        return ExpenseItem.objects.filter(report__report_id=report_id, report__user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Include presigned URL in context for POST requests
        if self.request.method == 'POST':
            context['include_presigned_url'] = True
        return context

    def perform_create(self, serializer):
        report_id = self.kwargs['report_id']
        logger.debug(f'Creating ExpenseItem for report_id: {report_id} and user: {self.request.user}')
        try:
            report = ExpenseReport.objects.get(report_id=report_id, user=self.request.user)
            serializer.save(report=report)
        except ExpenseReport.DoesNotExist:
            logger.error(f'ExpenseReport with id {report_id} does not exist for user {self.request.user}')
            raise

class ExpenseItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseItemSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'item_id'

    def get_queryset(self):
        report_id = self.kwargs['report_id']
        return ExpenseItem.objects.filter(report__report_id=report_id, report__user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Include presigned URL in context for PUT and PATCH requests
        if self.request.method in ['PUT', 'PATCH']:
            context['include_presigned_url'] = True
        return context
    
class ExpenseItemFileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, report_id, item_id, *args, **kwargs):
        try:
            expense_item = ExpenseItem.objects.get(report__report_id=report_id, item_id=item_id, report__user=request.user)
            if expense_item.s3_path:
                bucket_name = settings.AWS_S3_BUCKET_NAME
                presigned_url = generate_presigned_url(bucket_name, expense_item.s3_path, 'get_object')
                return JsonResponse({'presigned_url': presigned_url})
            else:
                return JsonResponse({'error': 'No file associated with this expense item'}, status=status.HTTP_404_NOT_FOUND)
        except ExpenseItem.DoesNotExist:
            logger.error(f'ExpenseItem with id {item_id} for report {report_id} does not exist for user {request.user}')
            return JsonResponse({'error': 'Expense item not found'}, status=status.HTTP_404_NOT_FOUND)
        
class ExpenseItemFileDeleteView(generics.GenericAPIView):
    serializer_class = ExpenseItemSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'item_id'

    def delete(self, request, report_id, item_id, *args, **kwargs):
        try:
            expense_item = ExpenseItem.objects.get(report__report_id=report_id, item_id=item_id, report__user=request.user)
            if expense_item.s3_path:
                delete_s3_file(settings.AWS_S3_BUCKET_NAME, expense_item.s3_path)
                expense_item.s3_path = None
                expense_item.save()
                return JsonResponse({'detail': 'File deleted successfully.'}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'detail': 'No file to delete.'}, status=status.HTTP_400_BAD_REQUEST)
        except ExpenseItem.DoesNotExist:
            logger.error(f'ExpenseItem with id {item_id} does not exist for user {request.user}')
            return JsonResponse({'error': 'Expense item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Failed to delete file for ExpenseItem with id {item_id}: {e}')
            return JsonResponse({'error': 'Failed to delete file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
