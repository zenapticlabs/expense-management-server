from django.urls import path, re_path
from .views import ExpenseReportListCreateView, ExpenseReportDetailView, SubmitReportView
from .expense_item_views import ExpenseItemFileDeleteView, ExpenseItemFileDownloadView, ExpenseItemListCreateView, ExpenseItemDetailView

urlpatterns = [
    # ExpenseReport URLs
    path('reports/', ExpenseReportListCreateView.as_view(), name='expense-report-list-create'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/$', ExpenseReportDetailView.as_view(), name='expense-report-detail'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/submit/$', SubmitReportView.as_view(), name='submit-report'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/items/$', ExpenseItemListCreateView.as_view(), name='expense-item-list-create'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/items/(?P<item_id>[0-9a-f-]+)/$', ExpenseItemDetailView.as_view(), name='expense-item-detail'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/items/(?P<item_id>[0-9a-f-]+)/download-receipt/$', ExpenseItemFileDownloadView.as_view(), name='expense-item-file-download'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/items/(?P<item_id>[0-9a-f-]+)/delete-receipt/$', ExpenseItemFileDeleteView.as_view(), name='expense-item-file-delete'),
    
]
