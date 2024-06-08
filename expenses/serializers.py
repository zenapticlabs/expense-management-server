import time
from rest_framework import serializers

from expense_management_server import settings
from expenses.utils import generate_presigned_url
from .models import ExpenseReport, ExpenseItem

from rest_framework import serializers

import time
from rest_framework import serializers
from expense_management_server import settings
from expenses.utils import generate_presigned_url
from .models import ExpenseItem

class ExpenseItemSerializer(serializers.ModelSerializer):
    airline = serializers.SerializerMethodField()
    rental_agency = serializers.SerializerMethodField()
    car_type = serializers.SerializerMethodField()
    meal_category = serializers.SerializerMethodField()
    relationship_to_pai = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    hotel_daily_base_rate = serializers.SerializerMethodField()
    mileage_rate = serializers.SerializerMethodField()
    presigned_url = serializers.SerializerMethodField()
    filename = serializers.CharField(write_only=True, allow_null=True, required=False)

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

    def get_hotel_daily_base_rate(self, obj):
        if obj.hotel_daily_base_rate:
            return {
                "country": obj.hotel_daily_base_rate.country,
                "city": obj.hotel_daily_base_rate.city,
                "amount": obj.hotel_daily_base_rate.amount,
                "currency": obj.hotel_daily_base_rate.currency,
            }
        return None

    def get_mileage_rate(self, obj):
        if obj.mileage_rate:
            return {
                "rate": obj.mileage_rate.rate,
                "title": obj.mileage_rate.title,
            }
        return None

    def get_presigned_url(self, obj):
        # Only generate presigned URL if context indicates it's a write operation
        if self.context.get('include_presigned_url', False):
            if obj.s3_path:
                bucket_name = settings.AWS_S3_BUCKET_NAME
                return generate_presigned_url(bucket_name, obj.s3_path)
        return None

    def create(self, validated_data):
        filename = validated_data.pop('filename', None)
        user_id = self.context['request'].user.id
        report_id = validated_data["report"].id
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
        return expense_item

    def update(self, instance, validated_data):
        filename = validated_data.pop('filename', None)
        presigned_url = None
        if filename:
            user_id = self.context['request'].user.id
            report_id = instance.report.id
            epoch_timestamp = int(time.time())
            object_name = f'{user_id}/{report_id}/{epoch_timestamp}_{filename}'
            bucket_name = settings.AWS_S3_BUCKET_NAME
            presigned_url = generate_presigned_url(bucket_name, object_name)
            instance.s3_path = object_name
            instance.presigned_url = presigned_url
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.s3_path:
            representation['filename'] = instance.s3_path.split('/')[-1]
        else:
            representation['filename'] = None

        # Only include presigned URL in representation if it was created or updated
        if self.context.get('include_presigned_url', False) and hasattr(instance, 'presigned_url') and instance.presigned_url:
            representation['presigned_url'] = instance.presigned_url
        return representation

class ExpenseReportSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    report_number = serializers.ReadOnlyField()
    report_status = serializers.ReadOnlyField()
    report_submit_date = serializers.ReadOnlyField()
    integration_status = serializers.ReadOnlyField()
    integration_date = serializers.ReadOnlyField()

    class Meta:
        model = ExpenseReport
        exclude = ['error_message']
        