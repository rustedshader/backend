# Location API Keys Documentation

## Overview

# Location API Keys Documentation

## Overview

The `/trips/{trip_id}/live-location` endpoint now supports flexible authentication - you can use **EITHER** a JWT token **OR** a location API key. This allows both authenticated users and external systems (like IoT devices) to post location data.

## Authentication Methods

### Option 1: JWT Token (User Authentication)

Use this for mobile apps and web applications where users are logged in.

**Header:**

```
Authorization: Bearer <your_jwt_token>
```

### Option 2: Location API Key (System Authentication)

Use this for tracking devices, IoT sensors, or external systems that don't have user context.

**Header:**

```
X-Location-API-Key: <one_of_the_valid_api_keys>
```

### Option 3: Both (Optional)

You can provide both headers, and the system will use JWT authentication if valid, falling back to API key if needed.

## Valid API Keys (Hardcoded)

The following API keys are currently hardcoded in `app/api/deps.py`:

1. `loc_api_key_001_tracking_device_alpha`
2. `loc_api_key_002_tracking_device_beta`
3. `loc_api_key_003_mobile_app_integration`
4. `loc_api_key_004_iot_sensor_network`
5. `loc_api_key_005_emergency_services`

## Usage

### Endpoint

```
POST /trips/{trip_id}/live-location
```

### Required Headers

```
Authorization: Bearer <your_jwt_token>
X-Location-API-Key: <one_of_the_valid_api_keys>
Content-Type: application/json
```

### Request Body

```json
{
  "latitude": 28.7041,
  "longitude": 77.1025
}
```

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/trips/1/live-location" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Location-API-Key: loc_api_key_003_mobile_app_integration" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.7041,
    "longitude": 77.1025
  }'
```

### Example Python Request

```python
import requests

url = "http://localhost:8000/trips/1/live-location"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "X-Location-API-Key": "loc_api_key_003_mobile_app_integration",
    "Content-Type": "application/json"
}
data = {
    "latitude": 28.7041,
    "longitude": 77.1025
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### Success Response

```json
{
  "status": "success",
  "message": "Location data received",
  "location_id": 123,
  "timestamp": "2025-11-06T10:30:00Z"
}
```

### Error Responses

#### Missing API Key

```json
{
  "detail": "Location API key is required"
}
```

Status: 401 Unauthorized

#### Invalid API Key

```json
{
  "detail": "Invalid location API key"
}
```

Status: 401 Unauthorized

#### Missing or Invalid JWT Token

```json
{
  "detail": "Could not validate credentials"
}
```

Status: 401 Unauthorized

## Security Notes

⚠️ **TODO for Production:**

1. Move API keys to environment variables
2. Store API keys in database with user/device associations
3. Implement API key rotation mechanism
4. Add rate limiting per API key
5. Log API key usage for audit trail
6. Add expiration dates for API keys

## Implementation Details

- **Location:** `app/api/deps.py` - `VALID_LOCATION_API_KEYS` set
- **Dependency:** `verify_location_api_key()` function
- **Endpoint:** `app/api/v1/routes/trips.py` - `receive_live_location()`
