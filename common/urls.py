# common/urls.py

from django.urls import path
from .views import AirlineListView, ExchangeRateListView, RentalAgencyListView, CarTypeListView, MealCategoryListView, RelationshipToPAIListView, CityListView, HotelDailyBaseRateListView, MileageRateListView

app_name = 'common'

urlpatterns = [
    path('airlines', AirlineListView.as_view(), name='airline-list'),
    path('rental-agencies', RentalAgencyListView.as_view(), name='rental-agency-list'),
    path('car-types', CarTypeListView.as_view(), name='car-type-list'),
    path('meal-categories', MealCategoryListView.as_view(), name='meal-category-list'),
    path('relationships-to-pai', RelationshipToPAIListView.as_view(), name='relationship-to-pai-list'),
    path('cities', CityListView.as_view(), name='city-list'),
    path('hotel-daily-base-rates', HotelDailyBaseRateListView.as_view(), name='hotel-daily-base-rate-list'),
    path('mileage-rates', MileageRateListView.as_view(), name='mileage-rate-list'),
    path('exchange-rates', ExchangeRateListView.as_view(), name='exchange-rates'),
]
