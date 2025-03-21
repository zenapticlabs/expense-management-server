import logging
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.conf import settings
from common.models import ExchangeRate
from expenses.utils import delete_s3_file, generate_presigned_url
from .models import ExpenseItem, ExpenseReport
from .serializers import ExpenseItemSerializer, ExpenseReceiptSerializer
from decimal import Decimal
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class ExpenseItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        report_id = self.kwargs['report_id']
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ExpenseItem.objects.filter(report__report_id=report_id)
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

# class ExpenseItemDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = ExpenseItemSerializer
#     permission_classes = [IsAuthenticated]
#     lookup_field = 'item_id'

#     def get_queryset(self):
#         report_id = self.kwargs['report_id']
#         if self.request.user.is_staff or self.request.user.is_superuser:
#             return ExpenseItem.objects.filter(report__report_id=report_id)
#         return ExpenseItem.objects.filter(report__report_id=report_id, report__user=self.request.user)

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         # Include presigned URL in context for PUT and PATCH requests
#         if self.request.method in ['PUT', 'PATCH']:
#             context['include_presigned_url'] = True
#         return context
    
class ExpenseItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseItemSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'item_id'

    def get_queryset(self):
        """Retrieve expense items based on user permissions."""
        report_id = self.kwargs['report_id']
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ExpenseItem.objects.filter(report__report_id=report_id)
        return ExpenseItem.objects.filter(report__report_id=report_id, report__user=self.request.user)

    def get_serializer_context(self):
        """Modify serializer context to include presigned URL for PUT and PATCH."""
        context = super().get_serializer_context()
        if self.request.method in ['PUT', 'PATCH']:
            context['include_presigned_url'] = True
        return context

    def destroy(self, request, *args, **kwargs):
        """Subtract the deleted expense amount from the report before deleting."""
        instance = self.get_object()

        report = instance.report
        if not report:
            return Response({"result": "error", "message": "Associated report not found."}, status=status.HTTP_400_BAD_REQUEST)

        old_receipt_amount = Decimal(instance.receipt_amount)
        old_receipt_currency = instance.receipt_currency

        old_rate = self.get_exchange_rate(old_receipt_currency, report.report_currency)
        if old_rate is None:
            old_rate = Decimal(1)

        old_converted_amount = old_receipt_amount * old_rate
        report.report_amount -= old_converted_amount
        report.save()

        self.perform_destroy(instance)

        return Response({"result": "success", "message": "Expense item deleted and report updated."}, status=status.HTTP_204_NO_CONTENT)
    
    def get_exchange_rate(self, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal(1)
        try:
            latest_rate = ExchangeRate.objects.latest('date_fetched')
            from_rate = ExchangeRate.objects.get(target_currency=from_currency, date_fetched=latest_rate.date_fetched).rate
            to_rate = ExchangeRate.objects.get(target_currency=to_currency, date_fetched=latest_rate.date_fetched).rate
            return to_rate / from_rate
        except ExchangeRate.DoesNotExist:
            raise ValidationError(f'Exchange rate for {from_currency} to {to_currency} does not exist.')

    
class ExpenseItemFileDownloadView(generics.ListAPIView):
    serializer_class = ExpenseReceiptSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_presigned_url'] = True
        context['read_presigned_url'] = True
        return context
    
    def get_queryset(self):
        report_id = self.kwargs.get('report_id')
        item_id = self.kwargs.get('item_id')

        if self.request.user.is_staff or self.request.user.is_superuser:
            expense_item = get_object_or_404(ExpenseItem, report__report_id=report_id, item_id=item_id)
        else:
            expense_item = get_object_or_404(ExpenseItem, report__report_id=report_id, item_id=item_id, report__user=self.request.user)

        return expense_item.receipts.all()
        
class ExpenseItemFileDeleteView(generics.GenericAPIView):
    serializer_class = ExpenseItemSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'item_id'

    def delete(self, request, report_id, item_id, *args, **kwargs):
        try:
            if self.request.user.is_staff or self.request.user.is_superuser:
                expense_item = ExpenseItem.objects.get(report__report_id=report_id, item_id=item_id)
            else:
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
