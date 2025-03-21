from decimal import Decimal
import logging
import time
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from common.models import Airline, CarType, City, ExchangeRate, HotelDailyBaseRate, MealCategory, MileageRate, RelationshipToPAI, RentalAgency
from expenses.utils import generate_presigned_url
from .models import ExpenseReceipt, ExpenseReport, ExpenseItem
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class HotelDailyBaseRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelDailyBaseRate
        fields = '__all__'

class MileageRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MileageRate
        fields = '__all__'

class ExpenseReceiptSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    upload_filename = serializers.CharField(write_only=True, required=False)
    presigned_url = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseReceipt
        fields = ["id", "filename", "upload_filename", "s3_path", "presigned_url", "uploaded_at"]

    def get_filename(self, obj):
        return obj.s3_path.split("/")[-1] if obj.s3_path else None

    def get_s3_path(self, obj):
        return obj.s3_path
    
    def get_presigned_url(self, obj):
        if self.context.get('include_presigned_url', False):
            if obj.s3_path:
                if self.context.get('read_presigned_url', False):
                    return generate_presigned_url(obj.s3_path, operation="get_object")
                else:
                    return generate_presigned_url(obj.s3_path)
        return None

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
    hotel_daily_base_rate = serializers.CharField(write_only=True, required=False, allow_null=True)
    mileage_rate = serializers.CharField(write_only=True, required=False, allow_null=True)
    receipts = ExpenseReceiptSerializer(many=True, required=False)

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
        
    def _get_hotel_base_rate(self, city):
        try:
            return HotelDailyBaseRate.objects.filter(city__iexact=city).first()
        except HotelDailyBaseRate.DoesNotExist:
            logger.error(f"HotelBaseRate does not exist for city: {city}")
            pass
        return None

    def _get_mileage_rate(self, org):
        try:
            return MileageRate.objects.filter(value__iexact=org).first()
        except MileageRate.DoesNotExist:
            logger.error(f"Mileage does not exist for org: {org}")
            pass
        return None
        
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
        expense_type = validated_data['expense_type']
        
        validated_data['airline'] = self._get_instance(Airline, validated_data.pop('airline', None))
        validated_data['rental_agency'] = self._get_instance(RentalAgency, validated_data.pop('rental_agency', None))
        validated_data['car_type'] = self._get_instance(CarType, validated_data.pop('car_type', None))
        validated_data['meal_category'] = self._get_instance(MealCategory, validated_data.pop('meal_category', None))
        validated_data['relationship_to_pai'] = self._get_instance(RelationshipToPAI, validated_data.pop('relationship_to_pai', None))
        validated_data['mileage_rate'] = self._get_mileage_rate(self.context['request'].user.company_code) if expense_type == "Mileage" else None

        city = validated_data.pop('city', None)
        validated_data['city'] = self._get_instance(City, city)
        validated_data['hotel_daily_base_rate'] = self._get_hotel_base_rate(city) if expense_type == "Hotel" else None
        
        receipts_data = validated_data.pop("receipts", [])
        logger.info(f"Saving Validated Data: {validated_data}")
        expense_item = super().create(validated_data)
        self._process_receipts(expense_item, receipts_data)
        self._update_report_amount(report, None, receipt_amount, None, receipt_currency)
        return expense_item
    
    def update(self, instance, validated_data):
        old_receipt_amount = Decimal(instance.receipt_amount)
        old_receipt_currency = instance.receipt_currency

        new_receipt_amount = Decimal(validated_data.get('receipt_amount', old_receipt_amount))
        new_receipt_currency = validated_data.get('receipt_currency', old_receipt_currency)
        expense_type = validated_data['expense_type'] or instance.expense_type
        validated_data['airline'] = self._get_instance(Airline, value=validated_data.pop('airline', None)) or instance.airline
        validated_data['rental_agency'] = self._get_instance(RentalAgency, value=validated_data.pop('rental_agency', None)) or instance.rental_agency
        validated_data['car_type'] = self._get_instance(CarType, value=validated_data.pop('car_type', None)) or instance.car_type
        validated_data['meal_category'] = self._get_instance(MealCategory, value=validated_data.pop('meal_category', None)) or instance.meal_category
        validated_data['relationship_to_pai'] = self._get_instance(RelationshipToPAI, value=validated_data.pop('relationship_to_pai', None)) or instance.relationship_to_pai
        validated_data['mileage_rate'] = self._get_mileage_rate(self.context['request'].user.company_code) if expense_type == "Mileage" else None

        city = validated_data.pop('city', None)
        validated_data['city'] = self._get_instance(City, city) or instance.city
        validated_data['hotel_daily_base_rate'] = self._get_hotel_base_rate(city) if expense_type == "Hotel" else None

        receipts_data = validated_data.pop("receipts", [])
        logger.info(f"Saving Validated Data: {validated_data}")
        updated_expense_item = super().update(instance, validated_data)

        self._process_receipts(updated_expense_item, receipts_data, delete_old=True)
        self._update_report_amount(instance.report, old_receipt_amount, new_receipt_amount, old_receipt_currency, new_receipt_currency)
        return updated_expense_item

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['id'] = representation.pop('item_id')
        representation['airline'] = self.get_airline(instance)
        representation['rental_agency'] = self.get_rental_agency(instance)
        representation['car_type'] = self.get_car_type(instance)
        representation['meal_category'] = self.get_meal_category(instance)
        representation['relationship_to_pai'] = self.get_relationship_to_pai(instance)
        representation['city'] = self.get_city(instance)

        return representation
    
    def _process_receipts(self, expense_item, receipts_data, delete_old=False):
        keep_receipts = [receipt["s3_path"] for receipt in receipts_data if "s3_path" in receipt]
        new_receipts = [receipt.get("upload_filename") for receipt in receipts_data if receipt.get("upload_filename")]

        if delete_old:
            expense_item.receipts.exclude(s3_path__in=keep_receipts).delete()

        report_id = expense_item.report.report_id
        expense_id = expense_item.item_id
        epoch_timestamp = int(time.time())

        for filename in new_receipts:
            object_name = f'{report_id}/{expense_id}/{epoch_timestamp}_{filename}'
            ExpenseReceipt.objects.create(expense_item=expense_item, s3_path=object_name)


class ExpenseReportSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='report_id', read_only=True)
    user = serializers.ReadOnlyField(source='user.email')
    report_number = serializers.ReadOnlyField()
    report_status = serializers.CharField(default="Open")
    integration_status = serializers.CharField(default="Pending")
    report_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0.0)

    class Meta:
        model = ExpenseReport
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['id'] = representation.pop('report_id', None)
        return representation
