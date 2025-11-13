"""
ML Engine for ECT Allocation Prediction
Combines CatBoost ML model with Gemini LLM for SMS generation
"""
import pandas as pd
import numpy as np
import os
from catboost import CatBoostClassifier, Pool
from django.conf import settings
import google.generativeai as genai

# Model path - try both .cbm and .bin extensions
MODEL_PATH_CBM = os.path.join(settings.BASE_DIR, 'data', 'ect_model.cbm')
MODEL_PATH_BIN = os.path.join(settings.BASE_DIR, 'data', 'ect_model.cbm')  # Will check for .bin too
model = None

# Initialize model on module load
def _load_model():
    global model
    if model is None:
        # Try .cbm first, then .bin
        model_path = None
        if os.path.exists(MODEL_PATH_CBM):
            model_path = MODEL_PATH_CBM
        elif os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'ect_allocation_model_v1.bin')):
            model_path = os.path.join(settings.BASE_DIR, 'data', 'ect_allocation_model_v1.bin')
        elif os.path.exists(os.path.join(settings.BASE_DIR, '..', 'ect_allocation_model-main', 'models', 'ect_allocation_model_v1.bin')):
            # Fallback to original location
            model_path = os.path.join(settings.BASE_DIR, '..', 'ect_allocation_model-main', 'models', 'ect_allocation_model_v1.bin')
        
        if model_path:
            try:
                model = CatBoostClassifier()
                model.load_model(model_path)
                print(f"[OK] Loaded ML model from: {model_path}")
            except Exception as e:
                print(f"Warning: Could not load ML model from {model_path}: {e}")
                model = None
        else:
            print("Warning: No ML model file found. Run 'python train_model.py' or copy model to data/ folder.")
    return model

# Load model
_load_model()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', getattr(settings, 'GEMINI_API_KEY', ''))
if GEMINI_API_KEY and GEMINI_API_KEY != '':
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Could not configure Gemini API: {e}")


def predict_ect(household):
    """
    Predict ECT amount using CatBoost model
    
    Args:
        household: Household model instance
        
    Returns:
        int: Predicted ECT amount (0, 5000, or 10000)
    """
    global model
    
    # Load model if not loaded
    if model is None:
        model = _load_model()
    
    # If model doesn't exist, return None (will use rule-based)
    if model is None:
        return None
    
    try:
        # Get damage status from latest assessment
        damage_status = 'NONE'
        if household.assessments.exists():
            latest_assessment = household.assessments.first()
            damage_status = latest_assessment.damage_status
        
        # Prepare features
        df = pd.DataFrame([{
            'Barangay_ID': household.barangay,
            'Flood_Depth_Meters': float(household.flood_depth),
            'House_Height_Meters': float(household.house_height),
            'House_Width_Meters': float(household.house_width),
            'Damage_Classification': damage_status,
            'Is_4Ps_Recipient': int(household.is_4ps)
        }])
        
        # Calculate flood height ratio
        df['Flood_Height_Ratio'] = np.minimum(
            df['Flood_Depth_Meters'] / df['House_Height_Meters'], 
            1.0
        )
        
        # Select features for prediction (must match training order)
        X = df[[
            'Barangay_ID',           # 0 - categorical
            'Flood_Depth_Meters',    # 1 - numeric
            'House_Height_Meters',   # 2 - numeric
            'House_Width_Meters',    # 3 - numeric
            'Damage_Classification', # 4 - categorical
            'Is_4Ps_Recipient',      # 5 - numeric (0/1)
            'Flood_Height_Ratio'     # 6 - numeric
        ]]
        
        # Use Pool to specify categorical features correctly
        cat_features = [0, 4]  # Barangay_ID and Damage_Classification are categorical
        pool = Pool(X, cat_features=cat_features)
        
        # Predict
        prediction = model.predict(pool)
        ect_amount = int(prediction[0])
        
        # Ensure valid ECT amounts (0, 5000, 10000)
        if ect_amount not in [0, 5000, 10000]:
            # Round to nearest valid amount
            if ect_amount < 2500:
                ect_amount = 0
            elif ect_amount < 7500:
                ect_amount = 5000
            else:
                ect_amount = 10000
        
        return ect_amount
        
    except Exception as e:
        print(f"Error in ML prediction: {e}")
        return None


def generate_sms(amount, household_id, brgy, status):
    """
    Generate empathetic Tagalog SMS using Gemini API or fallback template
    
    Args:
        amount: ECT amount (0, 5000, or 10000)
        household_id: Household ID
        brgy: Barangay name
        status: Damage status
        
    Returns:
        str: SMS message in Tagalog
    """
    # Fallback SMS template
    if amount == 0:
        return f"DSWD: {household_id} sa {brgy} ay {status}. Wala pong ECT. Apela sa MSWDO."
    
    status_txt = "lubos na nasira" if amount == 10000 else "bahagyang nasira"
    fallback_sms = f"DSWD-ECT: Aprubado ang PHP{amount:,} para sa {household_id} sa {brgy} dahil sa {status_txt}. Antayin ang LGU. #DSWDMayMalasakit"
    
    # Try Gemini API if configured
    if GEMINI_API_KEY and GEMINI_API_KEY != '':
        try:
            prompt = f"""You are a DSWD (Department of Social Welfare and Development) agent. Generate a compassionate, professional SMS message in Filipino/Tagalog to inform a household about their Emergency Cash Transfer (ECT) allocation.

Household Information:
- Household ID: {household_id}
- Barangay: {brgy}
- Damage Status: {status}
- ECT Amount: ₱{amount:,}

Requirements:
1. Be empathetic and professional
2. Use Filipino/Tagalog language
3. Keep it under 160 characters if possible
4. Include the ECT amount clearly
5. Provide next steps or contact information
6. Use #DSWDMayMalasakit hashtag

Generate the SMS message:"""
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            generated_text = response.text.strip()
            
            # Use generated text if valid
            if generated_text and len(generated_text) > 20:
                return generated_text
        except Exception as e:
            print(f"Warning: Gemini API error, using fallback: {e}")
    
    # Return fallback
    return fallback_sms


def train_catboost_ect_engine(df):
    """
    Train CatBoost model on synthetic data
    
    Args:
        df: DataFrame with features and target
        
    Returns:
        CatBoostClassifier: Trained model
    """
    # Define features
    feature_cols = [
        'Barangay_ID',
        'Flood_Depth_Meters',
        'House_Height_Meters',
        'House_Width_Meters',
        'Damage_Classification',
        'Is_4Ps_Recipient',
        'Flood_Height_Ratio'
    ]
    
    # Prepare data
    X = df[feature_cols]
    y = df['ECT_Amount']
    
    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Define categorical features
    cat_features = ['Barangay_ID', 'Damage_Classification']
    
    # Train model
    model = CatBoostClassifier(
        iterations=1000,
        learning_rate=0.1,
        depth=6,
        loss_function='MultiClass',
        verbose=100,
        random_seed=42
    )
    
    model.fit(
        X_train, y_train,
        cat_features=cat_features,
        eval_set=(X_test, y_test),
        early_stopping_rounds=50
    )
    
    return model

