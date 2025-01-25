from decimal import Decimal
import time
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from common.models import Airline, CarType, City, ExchangeRate, HotelDailyBaseRate, MealCategory, MileageRate, RelationshipToPAI, RentalAgency
from django.conf import settings
from expenses.utils import generate_presigned_url
from .models import ExpenseReport, ExpenseItem

class HotelDailyBaseRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelDailyBaseRate
        fields = '__all__'

class MileageRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MileageRate
        fields = '__all__'

class ExpenseItemSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='item_id', read_only=True)
    justification = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    airline = serializers.CharField(write_only=True, required=False, allow_null=True)
    rental_agency = serializers.CharField(write_only=True, required=False, allow_null=True)
    car_type = serializers.CharField(write_only=True, required=False, allow_null=True)
    meal_category = serializers.CharField(write_only=True, required=False, allow_null=True)
    relationship_to_pai = serializers.CharField(write_only=True, required=False, allow_null=True)
    city = serializers.CharField(write_only=True, required=False, allow_null=True)
    hotel_daily_base_rate = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    mileage_rate = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    presigned_url = serializers.SerializerMethodField()
    filename = serializers.CharField(write_only=True, allow_null=True, required=False)

    def _get_instance(self, model, value=None, pk=None):
        if pk is not None:
            try:
                return model.objects.get(pk=pk)
            except model.DoesNotExist:
                raise ValidationError(f'Invalid input: {model.__name__} with ID "{pk}" does not exist.')
        elif value is not None:
            try:
                return model.objects.get(value=value)
            except model.DoesNotExist:
                raise ValidationError(f'Invalid input: {model.__name__} with value "{value}" does not exist.')
        return None

    class Meta:
        model = ExpenseItem
        fields = '__all__'

    def get_airline(self, obj):
        return obj.airline.value if obj.airline else None

    def get_rental_agency(self, obj):
        return obj.rental_agency.value if obj.rental_agency else None

    def get_car_type(self, obj):
        return obj.car_type.value if obj.car_type else None

    def get_meal_category(self, obj):
        return obj.meal_category.value if obj.meal_category else None

    def get_relationship_to_pai(self, obj):
        return obj.relationship_to_pai.value if obj.relationship_to_pai else None

    def get_city(self, obj):
        return obj.city.value if obj.city else None

    def get_presigned_url(self, obj):
        if self.context.get('include_presigned_url', False):
            if obj.s3_path:
                bucket_name = settings.AWS_S3_BUCKET_NAME
                return generate_presigned_url(bucket_name, obj.s3_path)
        return None
    
    def _get_exchange_rate(self, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal(1)
        try:
            latest_rate = ExchangeRate.objects.latest('date_fetched')
            from_rate = ExchangeRate.objects.get(target_currency=from_currency, date_fetched=latest_rate.date_fetched).rate
            to_rate = ExchangeRate.objects.get(target_currency=to_currency, date_fetched=latest_rate.date_fetched).rate
            return to_rate / from_rate
        except ExchangeRate.DoesNotExist:
            raise ValidationError(f'Exchange rate for {from_currency} to {to_currency} does not exist.')
        
    def _update_report_amount(self, report, old_amount, new_amount, old_currency, new_currency):
        print(old_amount, new_amount, old_currency, new_currency)
        # Subtract the old amount
        if old_amount is not None:
            old_rate = self._get_exchange_rate(old_currency, report.report_currency)
            old_converted_amount = old_amount * old_rate
            report.report_amount -= old_converted_amount

        # Add the new amount
        if new_amount is not None:
            new_rate = self._get_exchange_rate(new_currency, report.report_currency)
            new_converted_amount = new_amount * new_rate
            report.report_amount += new_converted_amount
        
        report.save()

    def create(self, validated_data):
        report = validated_data['report']
        receipt_amount = Decimal(validated_data['receipt_amount'])
        receipt_currency = validated_data['receipt_currency']
        
        validated_data['airline'] = self._get_instance(Airline, validated_data.pop('airline', None))
        validated_data['rental_agency'] = self._get_instance(RentalAgency, validated_data.pop('rental_agency', None))
        validated_data['car_type'] = self._get_instance(CarType, validated_data.pop('car_type', None))
        validated_data['meal_category'] = self._get_instance(MealCategory, validated_data.pop('meal_category', None))
        validated_data['relationship_to_pai'] = self._get_instance(RelationshipToPAI, validated_data.pop('relationship_to_pai', None))
        validated_data['city'] = self._get_instance(City, validated_data.pop('city', None))
        validated_data['hotel_daily_base_rate'] = self._get_instance(HotelDailyBaseRate, pk=validated_data.pop('hotel_daily_base_rate', None))
        validated_data['mileage_rate'] = self._get_instance(MileageRate, pk=validated_data.pop('mileage_rate', None))

        filename = validated_data.pop('filename', None)
        user_id = self.context['request'].user.id
        report_id = validated_data["report"].report_id
        epoch_timestamp = int(time.time())
        presigned_url = None
        validated_data['s3_path'] = None
        if filename:
            object_name = f'{user_id}/{report_id}/{epoch_timestamp}_{filename}'
            bucket_name = settings.AWS_S3_BUCKET_NAME
            presigned_url = generate_presigned_url(bucket_name, object_name)
            validated_data['s3_path'] = object_name
        expense_item = super().create(validated_data)
        expense_item.presigned_url = presigned_url
        self._update_report_amount(report, None, receipt_amount, None, receipt_currency)
        return expense_item

    def update(self, instance, validated_data):
        old_receipt_amount = Decimal(instance.receipt_amount)
        old_receipt_currency = instance.receipt_currency

        new_receipt_amount = Decimal(validated_data.get('receipt_amount', old_receipt_amount))
        new_receipt_currency = validated_data.get('receipt_currency', old_receipt_currency)
        
        filename = validated_data.pop('filename', None)
        presigned_url = None
        if filename:
            user_id = self.context['request'].user.id
            report_id = instance.report.report_id
            epoch_timestamp = int(time.time())
            object_name = f'{user_id}/{report_id}/{epoch_timestamp}_{filename}'
            bucket_name = settings.AWS_S3_BUCKET_NAME
            presigned_url = generate_presigned_url(bucket_name, object_name)
            instance.s3_path = object_name
            instance.presigned_url = presigned_url

        instance.airline = self._get_instance(Airline, value=validated_data.pop('airline', None)) or instance.airline
        instance.rental_agency = self._get_instance(RentalAgency, value=validated_data.pop('rental_agency', None)) or instance.rental_agency
        instance.car_type = self._get_instance(CarType, value=validated_data.pop('car_type', None)) or instance.car_type
        instance.meal_category = self._get_instance(MealCategory, value=validated_data.pop('meal_category', None)) or instance.meal_category
        instance.relationship_to_pai = self._get_instance(RelationshipToPAI, value=validated_data.pop('relationship_to_pai', None)) or instance.relationship_to_pai
        instance.city = self._get_instance(City, value=validated_data.pop('city', None)) or instance.city
        instance.hotel_daily_base_rate = self._get_instance(HotelDailyBaseRate, pk=validated_data.pop('hotel_daily_base_rate', None)) or instance.hotel_daily_base_rate
        instance.mileage_rate = self._get_instance(MileageRate, pk=validated_data.pop('mileage_rate', None)) or instance.mileage_rate
        updated = super().update(instance, validated_data)
        self._update_report_amount(instance.report, old_receipt_amount, new_receipt_amount, old_receipt_currency, new_receipt_currency)
        return updated

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.s3_path:
            representation['filename'] = instance.s3_path.split('/')[-1]
        else:
            print("Doesnt Exist")
            representation['filename'] = None

        if self.context.get('include_presigned_url', False) and hasattr(instance, 'presigned_url') and instance.presigned_url:
            representation['presigned_url'] = instance.presigned_url
            
        representation['id'] = representation.pop('item_id')
        representation['airline'] = self.get_airline(instance)
        representation['rental_agency'] = self.get_rental_agency(instance)
        representation['car_type'] = self.get_car_type(instance)
        representation['meal_category'] = self.get_meal_category(instance)
        representation['relationship_to_pai'] = self.get_relationship_to_pai(instance)
        representation['city'] = self.get_city(instance)
        representation['hotel_daily_base_rate'] = HotelDailyBaseRateSerializer(instance.hotel_daily_base_rate).data if instance.hotel_daily_base_rate else None
        representation['mileage_rate'] = MileageRateSerializer(instance.mileage_rate).data if instance.mileage_rate else None

        return representation

class ExpenseReportSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='report_id', read_only=True)
    user = serializers.ReadOnlyField(source='user.id')
    report_number = serializers.ReadOnlyField()
    report_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = ExpenseReport
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['id'] = representation.pop('report_id')
        return representation

    def create(self, validated_data):
        validated_data.setdefault('report_status', "Open")
        validated_data.setdefault('integration_status', "Pending")
        validated_data.setdefault('report_amount', 0.0)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'report_amount' not in validated_data:
            validated_data['report_amount'] = instance.report_amount
        return super().update(instance, validated_data)
