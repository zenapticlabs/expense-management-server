from django.urls import path
from .views import ExpenseReportListCreateView, ExpenseReportDetailView
from .expense_item_views import ExpenseItemListCreateView, ExpenseItemDetailView

urlpatterns = [
    # ExpenseReport URLs
    path('reports/', ExpenseReportListCreateView.as_view(), name='expense-report-list-create'),
    path('reports/<int:pk>/', ExpenseReportDetailView.as_view(), name='expense-report-detail'),
    path('reports/<int:report_id>/items/', ExpenseItemListCreateView.as_view(), name='expense-item-list-create'),
    path('reports/<int:report_id>/items/<int:pk>/', ExpenseItemDetailView.as_view(), name='expense-item-detail'),
]
