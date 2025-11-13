from django.contrib import admin
from .models import Household, DisasterEvent, DamageAssessment


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ['name', 'barangay', 'address', 'contact_number', 'created_at']
    list_filter = ['barangay', 'created_at']
    search_fields = ['name', 'address', 'barangay', 'contact_number']


@admin.register(DisasterEvent)
class DisasterEventAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_occurred', 'is_active', 'created_at']
    list_filter = ['is_active', 'date_occurred']
    search_fields = ['name', 'description']


@admin.register(DamageAssessment)
class DamageAssessmentAdmin(admin.ModelAdmin):
    list_display = ['household', 'disaster', 'damage_status', 'recommended_ect_amount', 'assessed_at']
    list_filter = ['damage_status', 'disaster', 'assessed_at']
    search_fields = ['household__name', 'household__barangay', 'disaster__name']
    readonly_fields = ['recommended_ect_amount']
