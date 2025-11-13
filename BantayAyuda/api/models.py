from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Household(models.Model):
    """Stores permanent data for each household"""
    household_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=200)
    address = models.TextField()
    barangay = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    # ML Features
    flood_depth = models.FloatField(default=0.0, help_text="Flood depth in meters")
    house_height = models.FloatField(default=4.0, help_text="House height in meters")
    house_width = models.FloatField(default=8.0, help_text="House width in meters")
    is_4ps = models.BooleanField(default=False, help_text="Is 4Ps recipient")
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.household_id or self.name} - {self.barangay}"


class DisasterEvent(models.Model):
    """Lets you create new disasters so the app is reusable"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_occurred = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_occurred']

    def __str__(self):
        return self.name


class DamageAssessment(models.Model):
    """Link between Household and DisasterEvent - stores damage status and ECT amount"""
    
    class DamageStatus(models.TextChoices):
        NONE = 'NONE', 'No Damage'
        PARTIAL = 'PARTIAL', 'Partial Damage'
        TOTAL = 'TOTAL', 'Total Damage'

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='assessments')
    disaster = models.ForeignKey(DisasterEvent, on_delete=models.CASCADE, related_name='assessments')
    damage_status = models.CharField(max_length=10, choices=DamageStatus.choices, default=DamageStatus.NONE)
    recommended_ect_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    notes = models.TextField(blank=True)
    assessed_by = models.CharField(max_length=100, blank=True)
    assessed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['household', 'disaster']
        ordering = ['-assessed_at']

    def save(self, *args, **kwargs):
        """
        CRITICAL IMPLEMENTATION: Automatically implements the hackathon's core business logic.
        Uses PAYOUT_CRITERIA from PDF 1 (Page 2) and PDF 2 (Page 4):
        - TOTAL damage = ₱10,000
        - PARTIAL damage = ₱5,000
        - NONE damage = ₱0
        
        ML Override: If flood_depth > 0, use ML prediction instead of rule-based
        """
        # Rule-based (fallback)
        if self.damage_status == self.DamageStatus.TOTAL:
            self.recommended_ect_amount = 10000
        elif self.damage_status == self.DamageStatus.PARTIAL:
            self.recommended_ect_amount = 5000
        else:  # NONE
            self.recommended_ect_amount = 0
        
        # ML Override (if flood data exists) - disabled during bulk operations
        # ML predictions are handled via API endpoint /api/ml/predict/
        # Uncomment below if you want ML to override during save:
        # if self.household.flood_depth > 0:
        #     try:
        #         from .ml_engine import predict_ect
        #         ml_amount = predict_ect(self.household)
        #         if ml_amount is not None:
        #             self.recommended_ect_amount = ml_amount
        #     except Exception:
        #         # If ML fails, use rule-based
        #         pass
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.household.name} - {self.disaster.name}: {self.damage_status} (₱{self.recommended_ect_amount})"
