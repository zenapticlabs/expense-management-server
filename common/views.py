# common/views.py
import datetime
import time
import requests
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Airline, ExchangeRate, RentalAgency, CarType, MealCategory, RelationshipToPAI, City, HotelDailyBaseRate, MileageRate
from .serializers import AirlineSerializer, ExchangeRateSerializer, RentalAgencySerializer, CarTypeSerializer, MealCategorySerializer, RelationshipToPAISerializer, CitySerializer, HotelDailyBaseRateSerializer, MileageRateSerializer
from django.utils import timezone

class AirlineListView(generics.ListAPIView):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer

class RentalAgencyListView(generics.ListAPIView):
    queryset = RentalAgency.objects.all()
    serializer_class = RentalAgencySerializer

class CarTypeListView(generics.ListAPIView):
    queryset = CarType.objects.all()
    serializer_class = CarTypeSerializer

class MealCategoryListView(generics.ListAPIView):
    queryset = MealCategory.objects.all()
    serializer_class = MealCategorySerializer

class RelationshipToPAIListView(generics.ListAPIView):
    queryset = RelationshipToPAI.objects.all()
    serializer_class = RelationshipToPAISerializer

class CityListView(generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class HotelDailyBaseRateListView(generics.ListAPIView):
    queryset = HotelDailyBaseRate.objects.all()
    serializer_class = HotelDailyBaseRateSerializer

class MileageRateListView(generics.ListAPIView):
    queryset = MileageRate.objects.all()
    serializer_class = MileageRateSerializer
    
class ExchangeRateListView(generics.ListAPIView):
    serializer_class = ExchangeRateSerializer

    def get_queryset(self):
        latest_rate = ExchangeRate.objects.order_by('-date_fetched').first()
        if latest_rate:
            return ExchangeRate.objects.filter(date_fetched=latest_rate.date_fetched)
        return ExchangeRate.objects.none()

    def list(self, request, *args, **kwargs):
        base_currency = request.query_params.get('base', 'USD').upper()
        latest_rate = ExchangeRate.objects.order_by('-date_fetched').first()

        if not latest_rate or timezone.now() >= latest_rate.next_update_time:
            self.update_exchange_rates()

        latest_rate = ExchangeRate.objects.order_by('-date_fetched').first()
        
        queryset = ExchangeRate.objects.filter(date_fetched=latest_rate.date_fetched) if latest_rate else ExchangeRate.objects.none()

        if not queryset.exists():
            return Response(
                {"result": "error", "message": "No exchange rate data available"},
                status=status.HTTP_404_NOT_FOUND
            )

        if base_currency != 'USD':
            base_rate_obj = queryset.filter(target_currency=base_currency).first()
            if not base_rate_obj:
                return Response(
                    {"result": "error", "message": f"Base currency {base_currency} not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            usd_to_base_rate = base_rate_obj.rate
            conversion_rates = {rate.target_currency: rate.rate / usd_to_base_rate for rate in queryset}
        else:
            conversion_rates = {rate.target_currency: rate.rate for rate in queryset}

        return Response(conversion_rates, status=status.HTTP_200_OK)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        report = instance.report

        old_receipt_amount = Decimal(instance.receipt_amount)
        old_receipt_currency = instance.receipt_currency

        old_rate = self.get_exchange_rate(old_receipt_currency, report.report_currency)
        old_converted_amount = old_receipt_amount * old_rate
        report.report_amount -= old_converted_amount
        report.save()

        self.perform_destroy(instance)

        return Response({"result": "success", "message": "Expense item deleted and report updated."}, status=status.HTTP_204_NO_CONTENT)


    def update_exchange_rates(self):
        """Fetch latest exchange rates and update the database."""
        try:
            data = self.fetch_exchange_rates()
            
            if not data:
                print("Failed to fetch exchange rates after multiple attempts.")
                return
            
            conversion_rates = data['rates']
            last_update_time = timezone.now()
            next_update_time = timezone.make_aware(
                datetime.datetime.utcfromtimestamp(data['time_next_update_unix'])
            )

            for target_currency, rate in conversion_rates.items():
                ExchangeRate.objects.update_or_create(
                    target_currency=target_currency,
                    defaults={
                        'rate': rate,
                        'date_fetched': last_update_time,
                        'next_update_time': next_update_time
                    }
                )

        except Exception as e:
            print(f"Unexpected error updating exchange rates: {e}")


    def fetch_exchange_rates(self, max_retries=3, backoff_factor=1):
        url = 'https://open.er-api.com/v6/latest/USD'
        timeout = 5

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("Max retries reached. Giving up.")
                    return None

