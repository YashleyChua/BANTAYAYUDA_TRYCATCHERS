from rest_framework import serializers
from .models import Household, DisasterEvent, DamageAssessment


class HouseholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Household
        fields = '__all__'


class DisasterEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisasterEvent
        fields = '__all__'


class DamageAssessmentSerializer(serializers.ModelSerializer):
    household_name = serializers.CharField(source='household.name', read_only=True)
    household_address = serializers.CharField(source='household.address', read_only=True)
    household_contact = serializers.CharField(source='household.contact_number', read_only=True)
    disaster_name = serializers.CharField(source='disaster.name', read_only=True)

    class Meta:
        model = DamageAssessment
        fields = '__all__'

