# views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import ExpenseReport
from .serializers import ExpenseReportSerializer

# ExpenseReport views
class ExpenseReportListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
