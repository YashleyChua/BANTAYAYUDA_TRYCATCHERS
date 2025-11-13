"""
Management command to seed sample data for BantayAyuda.
Run with: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from api.models import Household, DisasterEvent, DamageAssessment
from decimal import Decimal
import random
import requests
import time


class Command(BaseCommand):
    help = 'Seeds the database with 50 NCR households (Tondo, Baseco, Navotas) and damage assessments'
    
    def _get_address_from_coordinates(self, lat, lon, barangay, area_name, streets):
        """
        Generate accurate address based on exact coordinates
        Uses coordinate ranges to determine specific area and street
        """
        house_number = random.randint(1, 999)
        
        # Determine specific area and street based on exact coordinates
        if barangay == 'Tondo':
            # North Tondo (higher latitude)
            if lat >= 14.6200:
                if 120.9650 <= lon <= 120.9750:
                    street = random.choice(['Juan Luna Street', 'Moriones Street', 'Dagupan Street'])
                    return f"{house_number} {street}, Barangay 105, Tondo, Manila"
                else:
                    street = random.choice(['Velasquez Street', 'P. Guevarra Street'])
                    return f"{house_number} {street}, Barangay 105, Tondo, Manila"
            # Central Tondo
            elif lat >= 14.6100:
                if 120.9600 <= lon <= 120.9700:
                    street = random.choice(['Tayuman Street', 'Abad Santos Avenue'])
                    return f"{house_number} {street}, Barangay 104, Tondo, Manila"
                else:
                    street = random.choice(['Rizal Avenue Extension', 'Capulong Street'])
                    return f"{house_number} {street}, Barangay 104, Tondo, Manila"
            # South Tondo
            else:
                street = random.choice(['Lakandula Street', 'M. Dela Fuente Street', 'Antonio Rivera Street'])
                return f"{house_number} {street}, Barangay 103, Tondo, Manila"
                
        elif barangay == 'Baseco':
            # Baseco Compound area
            if 14.5900 <= lat <= 14.5950:
                street = random.choice(['Baseco Road', 'Port Area Road'])
                return f"{house_number} {street}, Baseco Compound, Port Area, Manila"
            else:
                street = random.choice(['Baseco Boulevard', 'Baseco Main Street', 'Roxas Boulevard Extension'])
                return f"{house_number} {street}, Baseco Compound, Port Area, Manila"
                
        elif barangay == 'Navotas':
            # North Navotas
            if lat >= 14.6550:
                if 120.9400 <= lon <= 120.9500:
                    street = random.choice(['Navotas Boulevard', 'C-4 Road'])
                    return f"{house_number} {street}, Barangay San Roque, Navotas City"
                else:
                    street = random.choice(['M. Naval Street', 'San Roque Street'])
                    return f"{house_number} {street}, Barangay San Roque, Navotas City"
            # Central Navotas
            elif lat >= 14.6450:
                street = random.choice(['Tangos Street', 'Daanghari Road', 'Bagumbayan Street'])
                return f"{house_number} {street}, Barangay Tangos, Navotas City"
            # South Navotas
            else:
                street = random.choice(['San Jose Street', 'Navotas Fish Port Road', 'Bangus Street', 'Tanza Street'])
                return f"{house_number} {street}, Barangay Bagumbayan, Navotas City"
        
        # Final fallback
        street = random.choice(streets)
        return f"{house_number} {street}, {barangay}, {area_name}"

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed sample data...')
        
        # Create Disaster Event
        disaster, created = DisasterEvent.objects.get_or_create(
            name='Typhoon Rosing 2025',
            defaults={
                'description': 'A severe typhoon that affected multiple barangays in Metro Manila (NCR)',
                'date_occurred': '2025-11-10',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created disaster: {disaster.name}'))
        else:
            self.stdout.write(f'-> Disaster already exists: {disaster.name}')
        
        # NCR Barangays with accurate coordinates and real street names
        # Each entry: (barangay_name, base_lat, base_lon, max_offset, streets_list, area_name)
        barangays_data = [
            # Tondo - Manila (specific areas with real streets)
            ('Tondo', 14.6250, 120.9700, 0.008, 
             ['Juan Luna Street', 'Moriones Street', 'Dagupan Street', 'Velasquez Street', 
              'P. Guevarra Street', 'Tayuman Street', 'Abad Santos Avenue', 'Rizal Avenue Extension',
              'Capulong Street', 'Lakandula Street', 'M. Dela Fuente Street', 'Antonio Rivera Street'],
             'Tondo, Manila'),
            # Baseco - Manila (Baseco Compound area)
            ('Baseco', 14.5920, 120.9600, 0.006,
             ['Baseco Road', 'Port Area Road', 'Roxas Boulevard Extension', 'Baseco Compound',
              'Coastal Road', 'Baseco Boulevard', 'Port Road', 'Baseco Main Street'],
             'Baseco Compound, Port Area, Manila'),
            # Navotas - specific areas
            ('Navotas', 14.6550, 120.9450, 0.007,
             ['Navotas Boulevard', 'C-4 Road', 'M. Naval Street', 'San Roque Street',
              'Tangos Street', 'Daanghari Road', 'Bagumbayan Street', 'San Jose Street',
              'Navotas Fish Port Road', 'Bangus Street', 'Tanza Street', 'North Bay Boulevard'],
             'Navotas City'),
        ]
        
        # Generate 50 households
        random.seed(42)  # For reproducibility
        created_households = 0
        
        first_names = ['Juan', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Rosa', 'Jose', 'Lourdes', 'Roberto', 'Carmen',
                      'Ricardo', 'Elena', 'Fernando', 'Isabel', 'Miguel', 'Patricia', 'Antonio', 'Sofia', 'Manuel', 'Lucia']
        last_names = ['Dela Cruz', 'Santos', 'Garcia', 'Rodriguez', 'Mendoza', 'Villanueva', 'Torres', 'Fernandez',
                     'Cruz', 'Reyes', 'Ramos', 'Lopez', 'Gonzalez', 'Martinez', 'Perez', 'Sanchez', 'Rivera', 'Morales', 'Ortiz', 'Castillo']
        
        for i in range(50):
            brgy_name, base_lat, base_lon, max_offset, streets, area_name = random.choice(barangays_data)
            
            # Add smaller, more controlled random offset to keep coordinates on land
            lat = base_lat + random.uniform(-max_offset, max_offset)
            lon = base_lon + random.uniform(-max_offset, max_offset)
            
            # Ensure coordinates are within reasonable land boundaries
            if brgy_name == 'Tondo':
                lat = max(14.5800, min(14.6300, lat))
                lon = max(120.9500, min(120.9800, lon))
            elif brgy_name == 'Baseco':
                lat = max(14.5850, min(14.6000, lat))
                lon = max(120.9550, min(120.9700, lon))
            elif brgy_name == 'Navotas':
                lat = max(14.6400, min(14.6700, lat))
                lon = max(120.9300, min(120.9600, lon))
            
            # Generate household data
            household_id = f'HH-{i:05d}'
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Generate accurate address based on exact coordinates
            address = self._get_address_from_coordinates(lat, lon, brgy_name, area_name, streets)
            
            # ML features
            flood_depth = round(random.uniform(0, 4), 2)
            house_height = round(random.uniform(3, 8), 2)
            house_width = round(random.uniform(6, 12), 2)
            is_4ps = random.choice([True, False])
            
            household, created = Household.objects.get_or_create(
                household_id=household_id,
                defaults={
                    'name': name,
                    'address': address,
                    'barangay': brgy_name,
                    'latitude': Decimal(str(lat)),
                    'longitude': Decimal(str(lon)),
                    'flood_depth': flood_depth,
                    'house_height': house_height,
                    'house_width': house_width,
                    'is_4ps': is_4ps,
                    'contact_number': f'+63917{random.randint(1000000, 9999999)}'
                }
            )
            
            if created:
                created_households += 1
                
                # Create damage assessment based on flood depth
                if flood_depth > 3.0:
                    damage_status = DamageAssessment.DamageStatus.TOTAL
                elif flood_depth > 1.0:
                    damage_status = DamageAssessment.DamageStatus.PARTIAL
                else:
                    damage_status = DamageAssessment.DamageStatus.NONE
                
                # Add some randomness
                if random.random() < 0.1:  # 10% chance to override
                    damage_status = random.choice([
                        DamageAssessment.DamageStatus.TOTAL,
                        DamageAssessment.DamageStatus.PARTIAL,
                        DamageAssessment.DamageStatus.NONE
                    ])
                
                DamageAssessment.objects.create(
                    household=household,
                    disaster=disaster,
                    damage_status=damage_status,
                    notes=f'AI-generated assessment for {household.name}',
                    assessed_by='System Admin'
                )
        
        self.stdout.write(f'-> Created {created_households} new households')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n[OK] Sample data seeding completed!'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  - Disasters: {DisasterEvent.objects.count()}')
        self.stdout.write(f'  - Households: {Household.objects.count()}')
        self.stdout.write(f'  - Damage Assessments: {DamageAssessment.objects.count()}')
        self.stdout.write(f'\nYou can now access the dashboard at http://localhost:8000/')

