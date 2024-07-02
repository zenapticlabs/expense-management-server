# views.py
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ExpenseReport
from .serializers import ExpenseReportSerializer
from rest_framework.permissions import IsAdminUser

# ExpenseReport views
class ExpenseReportListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ExpenseReport.objects.all()
        return ExpenseReport.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            report_status="Open",
            report_submit_date=None,
            integration_status="Pending",
            integration_date=None
        )
class ExpenseReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseReportSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'report_id'

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ExpenseReport.objects.all()
        return ExpenseReport.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(
            user=self.request.user,
            report_status=serializer.instance.report_status,
            report_submit_date=serializer.instance.report_submit_date,
            integration_status=serializer.instance.integration_status,
            integration_date=serializer.instance.integration_date,
            error=serializer.instance.error
        )
        
class SubmitReportView(generics.UpdateAPIView):
    serializer_class = ExpenseReportSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'report_id'

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ExpenseReport.objects.all()
        return ExpenseReport.objects.filter(user=self.request.user, report_status="Open")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.report_status = "Submitted"
        instance.report_submit_date = timezone.now()
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UpdateReportStatusView(generics.UpdateAPIView):
    serializer_class = ExpenseReportSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'report_id'

    def get_queryset(self):
        return ExpenseReport.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.report_status = request.data.get("report_status", instance.report_status)
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

