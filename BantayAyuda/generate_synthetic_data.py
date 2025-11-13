"""
Generate synthetic data for training CatBoost ECT allocation model
"""
import pandas as pd
import numpy as np
import random


def generate_synthetic_data(n_samples=10000):
    """
    Generate synthetic household data for ECT allocation training
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with features and target ECT_Amount
    """
    np.random.seed(42)
    random.seed(42)
    
    # Barangays in NCR (Tondo, Baseco, Navotas)
    barangays = ['Tondo', 'Baseco', 'Navotas']
    
    # Generate data
    data = []
    
    for i in range(n_samples):
        # Random barangay
        barangay = random.choice(barangays)
        
        # Flood depth (0 to 5 meters)
        flood_depth = np.random.exponential(1.0)
        flood_depth = min(flood_depth, 5.0)
        
        # House dimensions
        house_height = np.random.normal(4.5, 1.0)
        house_height = max(2.0, min(house_height, 8.0))
        
        house_width = np.random.normal(8.0, 2.0)
        house_width = max(4.0, min(house_width, 15.0))
        
        # 4Ps recipient (30% chance)
        is_4ps = random.random() < 0.3
        
        # Calculate flood height ratio
        flood_height_ratio = min(flood_depth / house_height, 1.0)
        
        # Determine damage classification based on flood
        if flood_height_ratio > 0.8 or flood_depth > 3.5:
            damage_status = 'TOTAL'
        elif flood_height_ratio > 0.4 or flood_depth > 1.5:
            damage_status = 'PARTIAL'
        else:
            damage_status = 'NONE'
        
        # Determine ECT amount (with some randomness)
        if damage_status == 'TOTAL':
            ect_amount = 10000
        elif damage_status == 'PARTIAL':
            ect_amount = 5000
        else:
            ect_amount = 0
        
        # Add some noise: 4Ps recipients might get slightly higher priority
        if is_4ps and damage_status == 'PARTIAL' and random.random() < 0.1:
            ect_amount = 10000  # Upgrade to total damage payout
        elif is_4ps and damage_status == 'NONE' and flood_depth > 0.5 and random.random() < 0.05:
            ect_amount = 5000  # Upgrade to partial damage payout
        
        data.append({
            'Barangay_ID': barangay,
            'Flood_Depth_Meters': round(flood_depth, 2),
            'House_Height_Meters': round(house_height, 2),
            'House_Width_Meters': round(house_width, 2),
            'Damage_Classification': damage_status,
            'Is_4Ps_Recipient': int(is_4ps),
            'Flood_Height_Ratio': round(flood_height_ratio, 3),
            'ECT_Amount': ect_amount
        })
    
    df = pd.DataFrame(data)
    
    # Ensure balanced classes
    print(f"Generated {len(df)} samples")
    print(f"ECT Amount distribution:")
    print(df['ECT_Amount'].value_counts().sort_index())
    
    return df


if __name__ == '__main__':
    # Generate and save sample data
    df = generate_synthetic_data(10000)
    df.to_csv('data/synthetic_training_data.csv', index=False)
    print(f"\nSaved synthetic data to data/synthetic_training_data.csv")

