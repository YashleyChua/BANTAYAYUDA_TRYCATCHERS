from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
import requests
import json
from .models import Household, DisasterEvent, DamageAssessment
from .serializers import HouseholdSerializer, DisasterEventSerializer, DamageAssessmentSerializer
from .ml_engine import predict_ect, generate_sms as generate_sms_ml


class HouseholdViewSet(viewsets.ModelViewSet):
    """
    REST API ViewSet for Household model.
    Provides CRUD operations and a custom GeoJSON endpoint for the map.
    """
    queryset = Household.objects.all()
    serializer_class = HouseholdSerializer

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """
        CRITICAL IMPLEMENTATION: Custom GeoJSON endpoint for Leaflet.js map.
        This is the "magic" that builds your map.
        
        When frontend calls /api/households/geojson/?disaster_id=1, this function:
        1. Gets all Household locations
        2. Finds their DamageAssessment for that specific disaster
        3. Bundles it all into a single GeoJSON file that Leaflet.js can read
        
        Returns GeoJSON with colored markers based on damage_status:
        - Red: Total Damage (₱10,000)
        - Orange: Partial Damage (₱5,000)
        - Green: No Damage (₱0)
        """
        disaster_id = request.query_params.get('disaster_id', None)
        
        if not disaster_id:
            return Response(
                {'error': 'disaster_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            disaster = DisasterEvent.objects.get(pk=disaster_id)
        except DisasterEvent.DoesNotExist:
            return Response(
                {'error': 'Disaster not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Build GeoJSON structure
        features = []
        
        households = Household.objects.all()
        for household in households:
            # Get assessment for this household and disaster
            try:
                assessment = DamageAssessment.objects.get(
                    household=household,
                    disaster=disaster
                )
                damage_status = assessment.damage_status
                ect_amount = float(assessment.recommended_ect_amount)
            except DamageAssessment.DoesNotExist:
                damage_status = 'NONE'
                ect_amount = 0

            # Determine color based on damage status
            if damage_status == 'TOTAL':
                color = '#dc3545'  # Red
                marker_color = 'red'
            elif damage_status == 'PARTIAL':
                color = '#fd7e14'  # Orange
                marker_color = 'orange'
            else:
                color = '#28a745'  # Green
                marker_color = 'green'

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [
                        float(household.longitude),
                        float(household.latitude)
                    ]
                },
                'properties': {
                    'id': household.id,
                    'name': household.name,
                    'address': household.address,
                    'barangay': household.barangay,
                    'contact_number': household.contact_number or '',
                    'damage_status': damage_status,
                    'ect_amount': ect_amount,
                    'marker_color': marker_color,
                    'popup_content': f"""
                        <strong>{household.name}</strong><br>
                        {household.address}<br>
                        <strong>Status:</strong> {damage_status}<br>
                        <strong>ECT Amount:</strong> ₱{ect_amount:,.2f}
                    """
                }
            }
            features.append(feature)

        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }

        return JsonResponse(geojson)


class DisasterEventViewSet(viewsets.ModelViewSet):
    """REST API ViewSet for DisasterEvent model."""
    queryset = DisasterEvent.objects.all()
    serializer_class = DisasterEventSerializer


class DamageAssessmentViewSet(viewsets.ModelViewSet):
    """REST API ViewSet for DamageAssessment model."""
    queryset = DamageAssessment.objects.all()
    serializer_class = DamageAssessmentSerializer

    def get_queryset(self):
        """
        Optionally filter by disaster_id or household_id
        """
        queryset = DamageAssessment.objects.all()
        disaster_id = self.request.query_params.get('disaster_id', None)
        household_id = self.request.query_params.get('household_id', None)
        
        if disaster_id:
            queryset = queryset.filter(disaster_id=disaster_id)
        if household_id:
            queryset = queryset.filter(household_id=household_id)
            
        return queryset


# Gemini API endpoint for SMS generation
@api_view(['POST'])
def generate_sms(request):
    """
    LLM Integration: Generate SMS using Gemini API.
    This implements the "Innovation" and "AI/LLM" criteria from the PDFs.
    
    Takes household data and generates an empathetic SMS message in Filipino/Tagalog.
    """
    try:
        data = request.data
        prompt = data.get('prompt', '')
        household_name = data.get('household_name', '')
        damage_status = data.get('damage_status', '')
        ect_amount = data.get('ect_amount', 0)
        
        # Get Gemini API key from settings
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        
        if not api_key:
            return Response({
                'success': False,
                'error': 'Gemini API key not configured. Please set GEMINI_API_KEY in settings.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Call Gemini API
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}'
        
        payload = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract the generated text from Gemini response
            if 'candidates' in result and len(result['candidates']) > 0:
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                
                return Response({
                    'success': True,
                    'sms_message': generated_text.strip(),
                    'household_name': household_name,
                    'damage_status': damage_status,
                    'ect_amount': ect_amount
                })
            else:
                return Response({
                    'success': False,
                    'error': 'No response from Gemini API'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'error': f'Gemini API error: {response.status_code} - {response.text}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ML Prediction endpoint
@api_view(['GET'])
def ml_predict_view(request):
    """
    ML Prediction endpoint: Runs CatBoost ML model to predict ECT amounts
    and generates SMS messages for all households in a disaster.
    
    Returns:
        List of households with ML-predicted ECT amounts and SMS messages
    """
    disaster_id = request.GET.get('disaster_id')
    
    if not disaster_id:
        return Response(
            {'error': 'disaster_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        disaster = DisasterEvent.objects.get(pk=disaster_id)
    except DisasterEvent.DoesNotExist:
        return Response(
            {'error': 'Disaster not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get all assessments for this disaster
    assessments = DamageAssessment.objects.filter(disaster_id=disaster_id)
    
    results = []
    for assessment in assessments:
        household = assessment.household
        
        # Get ML prediction
        ect_amount = predict_ect(household)
        
        # If ML prediction failed, use assessment amount
        if ect_amount is None:
            ect_amount = int(float(assessment.recommended_ect_amount))
        
        # Generate SMS
        household_id = household.household_id or household.name
        sms = generate_sms_ml(
            ect_amount, 
            household_id, 
            household.barangay, 
            assessment.damage_status
        )
        
        results.append({
            'household_id': household_id,
            'household_name': household.name,
            'barangay': household.barangay,
            'lat': float(household.latitude),
            'lon': float(household.longitude),
            'ect_amount': ect_amount,
            'damage_status': assessment.damage_status,
            'flood_depth': household.flood_depth,
            'is_4ps': household.is_4ps,
            'sms': sms
        })
    
    return Response(results)


# Budget Summary endpoint
@api_view(['GET'])
def budget_summary_view(request):
    """
    Get budget summary and statistics for a disaster
    """
    disaster_id = request.GET.get('disaster_id')
    
    if not disaster_id:
        return Response(
            {'error': 'disaster_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        disaster = DisasterEvent.objects.get(pk=disaster_id)
    except DisasterEvent.DoesNotExist:
        return Response(
            {'error': 'Disaster not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get all assessments
    assessments = DamageAssessment.objects.filter(disaster_id=disaster_id)
    
    # Calculate statistics
    total_budget = 0
    total_households = assessments.count()
    by_status = {'TOTAL': 0, 'PARTIAL': 0, 'NONE': 0}
    by_barangay = {}
    by_amount = {0: 0, 5000: 0, 10000: 0}
    total_4ps = 0
    
    for assessment in assessments:
        household = assessment.household
        amount = int(float(assessment.recommended_ect_amount))
        
        total_budget += amount
        by_status[assessment.damage_status] = by_status.get(assessment.damage_status, 0) + 1
        by_amount[amount] = by_amount.get(amount, 0) + 1
        
        if household.barangay not in by_barangay:
            by_barangay[household.barangay] = {'count': 0, 'budget': 0}
        by_barangay[household.barangay]['count'] += 1
        by_barangay[household.barangay]['budget'] += amount
        
        if household.is_4ps:
            total_4ps += 1
    
    return Response({
        'disaster_name': disaster.name,
        'total_households': total_households,
        'total_budget': total_budget,
        'by_status': by_status,
        'by_barangay': by_barangay,
        'by_amount': by_amount,
        'total_4ps': total_4ps,
        'average_per_household': round(total_budget / total_households, 2) if total_households > 0 else 0
    })


# Export to CSV endpoint
@api_view(['GET'])
def export_csv_view(request):
    """
    Export assessment data to CSV
    """
    from django.http import HttpResponse
    import csv
    
    disaster_id = request.GET.get('disaster_id')
    
    if not disaster_id:
        return Response(
            {'error': 'disaster_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        disaster = DisasterEvent.objects.get(pk=disaster_id)
    except DisasterEvent.DoesNotExist:
        return Response(
            {'error': 'Disaster not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get all assessments
    assessments = DamageAssessment.objects.filter(disaster_id=disaster_id).select_related('household')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bantayayuda_export_{disaster.name.replace(" ", "_")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Household ID', 'Name', 'Address', 'Barangay', 
        'Latitude', 'Longitude', 'Damage Status', 'ECT Amount (PHP)',
        'Flood Depth (m)', 'House Height (m)', 'House Width (m)', '4Ps Recipient'
    ])
    
    for assessment in assessments:
        household = assessment.household
        writer.writerow([
            household.household_id or '',
            household.name,
            household.address,
            household.barangay,
            float(household.latitude),
            float(household.longitude),
            assessment.damage_status,
            int(float(assessment.recommended_ect_amount)),
            household.flood_depth,
            household.house_height,
            household.house_width,
            'Yes' if household.is_4ps else 'No'
        ])
    
    return response
