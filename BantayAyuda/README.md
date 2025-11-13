# BantayAyuda - DSWD ECT Allocation System

A Django-based web application for transparent allocation of DSWD Emergency Cash Transfer (ECT) funds (₱5,000/₱10,000) based on disaster damage assessments.

## Features

- **GIS Dashboard**: Interactive map using Leaflet.js and OpenStreetMap showing household damage status
- **REST API**: Full CRUD operations for households, disasters, and damage assessments
- **AI/ML Integration**: Ready for CatBoost model integration for damage prediction
- **LLM Integration**: Gemini API integration for generating empathetic SMS messages in Filipino/Tagalog
- **Transparent Allocation**: Automatic ECT amount calculation based on damage status:
  - Total Damage: ₱10,000
  - Partial Damage: ₱5,000
  - No Damage: ₱0

## Tech Stack

- **Backend**: Django 5.2.8, Django REST Framework
- **Frontend**: HTML5, JavaScript, Leaflet.js
- **Database**: SQLite (default, can be changed to PostgreSQL/MySQL)
- **AI/LLM**: Google Gemini API
- **Mapping**: OpenStreetMap + Leaflet.js

## Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up the database**:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Seed sample data** (IMPORTANT - Run this to get sample disasters and households):
```bash
python manage.py seed_data
```

4. **Create a superuser** (optional, for admin access):
```bash
python manage.py createsuperuser
```

5. **Configure Gemini API Key** (optional, for SMS generation):
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Add it to `BantayAyuda/settings.py`:
   ```python
   GEMINI_API_KEY = 'your-api-key-here'
   ```

6. **Run the development server**:
```bash
python manage.py runserver
```

7. **Access the application**:
   - Main dashboard: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/
   - API endpoints: http://localhost:8000/api/

## Sample Data

The `seed_data` management command creates:
- 1 disaster event: "Typhoon Rosing"
- 10 sample households in Metro Manila area
- 10 damage assessments with mixed statuses (Total, Partial, None)

To add more sample data, run:
```bash
python manage.py seed_data
```

## Project Structure

```
BantayAyuda/
├── api/
│   ├── models.py          # Database models (Household, DisasterEvent, DamageAssessment)
│   ├── views.py           # REST API views and GeoJSON endpoint
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # API URL routing
│   ├── admin.py           # Django admin configuration
│   └── management/
│       └── commands/
│           └── seed_data.py  # Management command to seed sample data
├── templates/
│   └── index.html         # Frontend dashboard with Leaflet.js map
├── BantayAyuda/
│   ├── settings.py        # Django settings
│   └── urls.py            # Main URL configuration
└── requirements.txt       # Python dependencies
```

## API Endpoints

### Households
- `GET /api/households/` - List all households
- `POST /api/households/` - Create a new household
- `GET /api/households/{id}/` - Get household details
- `PUT /api/households/{id}/` - Update household
- `DELETE /api/households/{id}/` - Delete household
- `GET /api/households/geojson/?disaster_id={id}` - Get GeoJSON for map

### Disasters
- `GET /api/disasters/` - List all disasters
- `POST /api/disasters/` - Create a new disaster
- `GET /api/disasters/{id}/` - Get disaster details
- `PUT /api/disasters/{id}/` - Update disaster
- `DELETE /api/disasters/{id}/` - Delete disaster

### Damage Assessments
- `GET /api/assessments/` - List all assessments
- `POST /api/assessments/` - Create a new assessment
- `GET /api/assessments/{id}/` - Get assessment details
- `PUT /api/assessments/{id}/` - Update assessment
- `DELETE /api/assessments/{id}/` - Delete assessment

### SMS Generation
- `POST /api/generate-sms/` - Generate SMS using Gemini API
  ```json
  {
    "prompt": "Your prompt here",
    "household_name": "Juan Dela Cruz",
    "damage_status": "TOTAL",
    "ect_amount": 10000
  }
  ```

## Usage

1. **Seed Sample Data** (First time setup):
   ```bash
   python manage.py seed_data
   ```

2. **Access the Dashboard**:
   - Open http://localhost:8000/
   - Select a disaster from the dropdown
   - Click "Load Households on Map"
   - See color-coded markers:
     - 🔴 Red: Total Damage (₱10,000)
     - 🟠 Orange: Partial Damage (₱5,000)
     - 🟢 Green: No Damage (₱0)

3. **Generate SMS**:
   - Select a household from the dropdown
   - Click "Generate SMS Message"
   - View the AI-generated message in Filipino/Tagalog

4. **Add More Data via Admin**:
   - Go to http://localhost:8000/admin/
   - Login with superuser credentials
   - Add/edit disasters, households, and assessments

## Business Logic

The core business logic is implemented in `api/models.py` in the `DamageAssessment.save()` method:

```python
if damage_status == 'TOTAL':
    recommended_ect_amount = 10000
elif damage_status == 'PARTIAL':
    recommended_ect_amount = 5000
else:  # NONE
    recommended_ect_amount = 0
```

This ensures transparent, automatic allocation based on the hackathon's payout criteria.

## Troubleshooting

### No disasters loading?
- Run `python manage.py seed_data` to create sample data
- Check that migrations are applied: `python manage.py migrate`
- Check browser console for errors

### Buttons not working?
- Make sure you've selected a disaster first
- Check browser console for JavaScript errors
- Verify the API is running: http://localhost:8000/api/disasters/

### Map not showing?
- Check that households have valid latitude/longitude coordinates
- Verify GeoJSON endpoint: http://localhost:8000/api/households/geojson/?disaster_id=1
- Check browser console for Leaflet.js errors

## Development Notes

- The system is designed to integrate with a CatBoost ML model for damage prediction
- The "Run ML Assessment" button in the frontend is ready for ML model integration
- All API endpoints support CORS for frontend integration
- The GeoJSON endpoint is optimized for Leaflet.js map rendering

## License

This project was developed for the iACADEMY HACKAMARE hackathon.
