from django.urls import path, re_path
from .views import ExpenseReportListCreateView, ExpenseReportDetailView
from .expense_item_views import ExpenseItemListCreateView, ExpenseItemDetailView

urlpatterns = [
    # ExpenseReport URLs
    path('reports/', ExpenseReportListCreateView.as_view(), name='expense-report-list-create'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/items/$', ExpenseItemListCreateView.as_view(), name='expense-item-list-create'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/items/(?P<item_id>[0-9a-f-]+)/$', ExpenseItemDetailView.as_view(), name='expense-item-detail'),
    re_path(r'^reports/(?P<report_id>[0-9a-f-]+)/$', ExpenseReportDetailView.as_view(), name='expense-report-detail'),
]
