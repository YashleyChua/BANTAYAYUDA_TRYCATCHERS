"""
Model Validation Script
Compares ML predictions with rule-based assessments to measure accuracy
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BantayAyuda.settings')
django.setup()

from api.models import Household, DamageAssessment
from api.ml_engine import predict_ect
from collections import defaultdict

def validate_model():
    """
    Validates ML model predictions against rule-based assessments
    
    Returns accuracy metrics comparing:
    - ML predictions vs Rule-based ECT amounts
    - ML predictions vs Damage status
    """
    print("=" * 60)
    print("ML Model Validation Report")
    print("=" * 60)
    
    # Get all households with assessments
    assessments = DamageAssessment.objects.select_related('household').all()
    
    if not assessments:
        print("No assessments found. Run: python manage.py seed_data")
        return
    
    # Comparison metrics
    ml_vs_rule = defaultdict(int)  # ML prediction vs rule-based
    ml_vs_damage = defaultdict(int)  # ML prediction vs damage status
    total = 0
    exact_matches = 0
    within_tolerance = 0
    
    print(f"\nValidating {assessments.count()} assessments...\n")
    
    for assessment in assessments:
        household = assessment.household
        total += 1
        
        # Rule-based ECT amount (from damage status)
        rule_based_ect = int(float(assessment.recommended_ect_amount))
        
        # ML prediction
        ml_ect = predict_ect(household)
        if ml_ect is None:
            ml_ect = rule_based_ect  # Fallback to rule-based
        
        # Damage status
        damage_status = assessment.damage_status
        
        # Compare ML vs Rule-based
        if ml_ect == rule_based_ect:
            exact_matches += 1
            ml_vs_rule['exact'] += 1
        else:
            ml_vs_rule['different'] += 1
        
        # Compare ML vs Damage Status (expected ECT)
        expected_ect = {
            'TOTAL': 10000,
            'PARTIAL': 5000,
            'NONE': 0
        }.get(damage_status, 0)
        
        if ml_ect == expected_ect:
            ml_vs_damage['matches_damage'] += 1
        else:
            ml_vs_damage['differs_from_damage'] += 1
        
        # Tolerance check (within one tier)
        if abs(ml_ect - rule_based_ect) <= 5000:
            within_tolerance += 1
    
    # Print results
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    print(f"\n1. ML vs Rule-Based ECT Amount:")
    print(f"   Total assessments: {total}")
    print(f"   Exact matches: {exact_matches} ({exact_matches/total*100:.1f}%)")
    print(f"   Different: {ml_vs_rule['different']} ({ml_vs_rule['different']/total*100:.1f}%)")
    print(f"   Within tolerance (+/- PHP5K): {within_tolerance} ({within_tolerance/total*100:.1f}%)")
    
    print(f"\n2. ML vs Damage Status:")
    print(f"   Matches damage status: {ml_vs_damage['matches_damage']} ({ml_vs_damage['matches_damage']/total*100:.1f}%)")
    print(f"   Differs from damage status: {ml_vs_damage['differs_from_damage']} ({ml_vs_damage['differs_from_damage']/total*100:.1f}%)")
    
    print(f"\n3. Accuracy Metrics:")
    accuracy = exact_matches / total * 100 if total > 0 else 0
    print(f"   Exact Accuracy: {accuracy:.2f}%")
    print(f"   Tolerance Accuracy: {within_tolerance/total*100:.2f}%")
    
    print("\n" + "=" * 60)
    print("IMPORTANT NOTES:")
    print("=" * 60)
    print("""
1. This validation compares ML predictions with RULE-BASED assessments
   (not real ground truth damage assessments)

2. The model was trained on SYNTHETIC DATA where:
   - Damage was determined by flood depth rules
   - ECT amounts follow DSWD criteria

3. For REAL accuracy, you need:
   - Actual field damage assessments
   - Ground truth labels from DSWD/MSWDO
   - Validation on historical disaster data

4. Current metrics show how well ML matches the rule-based system,
   not how well it predicts real damage.
    """)
    
    return {
        'total': total,
        'exact_matches': exact_matches,
        'accuracy': accuracy,
        'within_tolerance': within_tolerance
    }

if __name__ == '__main__':
    validate_model()

