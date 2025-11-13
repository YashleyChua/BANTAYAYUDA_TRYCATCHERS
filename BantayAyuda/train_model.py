"""
Train CatBoost model for ECT allocation prediction
Run this once to generate the model: python train_model.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BantayAyuda.settings')
django.setup()

from generate_synthetic_data import generate_synthetic_data
from api.ml_engine import train_catboost_ect_engine

if __name__ == '__main__':
    print("=" * 60)
    print("Training CatBoost ECT Allocation Model")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate synthetic data
    print("\n1. Generating synthetic training data...")
    df = generate_synthetic_data(10000)
    print(f"   Generated {len(df)} samples")
    
    # Train model
    print("\n2. Training CatBoost model...")
    model = train_catboost_ect_engine(df)
    print("   Model training completed!")
    
    # Save model
    model_path = os.path.join(data_dir, 'ect_model.cbm')
    model.save_model(model_path)
    print(f"\n3. Model saved to: {model_path}")
    
    # Print model info
    print("\n" + "=" * 60)
    print("Model Training Complete!")
    print("=" * 60)
    print(f"Model file: {model_path}")
    print(f"Model size: {os.path.getsize(model_path) / 1024:.2f} KB")
    print("\nYou can now use the model for ECT predictions!")

