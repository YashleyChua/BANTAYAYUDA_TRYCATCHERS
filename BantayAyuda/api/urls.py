from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HouseholdViewSet, DisasterEventViewSet, DamageAssessmentViewSet, generate_sms, ml_predict_view, budget_summary_view, export_csv_view

router = DefaultRouter()
router.register(r'households', HouseholdViewSet, basename='household')
router.register(r'disasters', DisasterEventViewSet, basename='disaster')
router.register(r'assessments', DamageAssessmentViewSet, basename='assessment')

urlpatterns = [
    path('', include(router.urls)),
    path('generate-sms/', generate_sms, name='generate-sms'),
    path('ml/predict/', ml_predict_view, name='ml_predict'),
    path('budget/summary/', budget_summary_view, name='budget_summary'),
    path('export/csv/', export_csv_view, name='export_csv'),
]

