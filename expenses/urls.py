from django.urls import path, include
from .views import ExpenseReportListCreateView, ExpenseReportDetailView, SubmitReportView, UpdateReportStatusView
from .expense_item_views import ExpenseItemFileDeleteView, ExpenseItemFileDownloadView, ExpenseItemListCreateView, ExpenseItemDetailView

report_item_patterns = [
    path('', ExpenseItemListCreateView.as_view(), name='expense-item-list-create'),
    path('/<uuid:item_id>', ExpenseItemDetailView.as_view(), name='expense-item-detail'),
    path('/<uuid:item_id>/download-receipt', ExpenseItemFileDownloadView.as_view(), name='expense-item-file-download'),
    path('/<uuid:item_id>/delete-receipt', ExpenseItemFileDeleteView.as_view(), name='expense-item-file-delete'),
]

report_patterns = [
    path('', ExpenseReportListCreateView.as_view(), name='expense-report-list-create'),
    path('/<uuid:report_id>', ExpenseReportDetailView.as_view(), name='expense-report-detail'),
    path('/<uuid:report_id>/submit', SubmitReportView.as_view(), name='submit-report'),
    path('/<uuid:report_id>/status', UpdateReportStatusView.as_view(), name='update-report-status'),
    path('/<uuid:report_id>/items', include(report_item_patterns)),
]

urlpatterns = [
    path('reports', include(report_patterns)),
]