# Alert Management API Documentation

## Overview

The Alert Management API provides endpoints for creating, managing, and monitoring alerts within the SIH tourism safety system. Alerts are critical safety notifications that can be triggered for various situations including route deviations, emergencies, weather conditions, and other safety concerns.

## Alert Types

- **DEVIATION**: Tourist has deviated from planned route
- **EMERGENCY**: Emergency situation requiring immediate attention
- **WEATHER**: Weather-related safety alerts
- **OTHER**: Other types of alerts

## Alert Statuses

- **NEW**: Alert has been created but not yet acknowledged
- **ACKNOWLEDGED**: Alert has been seen and acknowledged by relevant personnel
- **RESOLVED**: Alert has been resolved and no further action needed

## API Endpoints

### Create Alert

**POST** `/alerts/`

Create a new alert for a trip.

**Request Body:**

```json
{
  "trip_id": 123,
  "alert_type": "EMERGENCY",
  "description": "Tourist has not responded to check-in for 2 hours",
  "location": {
    "latitude": 28.7041,
    "longitude": 77.1025
  }
}
```

**Response:**

```json
{
  "id": 456,
  "trip_id": 123,
  "timestamp": 1693478400,
  "alert_type": "EMERGENCY",
  "description": "Tourist has not responded to check-in for 2 hours",
  "location": {
    "latitude": 28.7041,
    "longitude": 77.1025
  },
  "status": "NEW"
}
```

### Get Emergency Alerts

**GET** `/alerts/emergency`

Get all active emergency alerts (NEW or ACKNOWLEDGED status). Admin only.

**Response:**

```json
[
  {
    "id": 456,
    "trip_id": 123,
    "timestamp": 1693478400,
    "alert_type": "EMERGENCY",
    "description": "Tourist has not responded to check-in for 2 hours",
    "location": {
      "latitude": 28.7041,
      "longitude": 77.1025
    },
    "status": "NEW"
  }
]
```

### Get Alert Statistics

**GET** `/alerts/statistics`

Get comprehensive statistics about alerts. Admin only.

**Response:**

```json
{
  "total_alerts": 150,
  "new_alerts": 12,
  "acknowledged_alerts": 8,
  "resolved_alerts": 130,
  "emergency_alerts": 5,
  "deviation_alerts": 45,
  "weather_alerts": 20,
  "other_alerts": 80
}
```

### Get Trip Alerts

**GET** `/alerts/trip/{trip_id}`

Get all alerts for a specific trip with optional filtering.

**Query Parameters:**

- `status` (optional): Filter by alert status (NEW, ACKNOWLEDGED, RESOLVED)
- `alert_type` (optional): Filter by alert type (DEVIATION, EMERGENCY, WEATHER, OTHER)
- `skip` (optional): Number of alerts to skip (default: 0)
- `limit` (optional): Maximum number of alerts to return (default: 100, max: 1000)

**Example:** `/alerts/trip/123?status=NEW&alert_type=EMERGENCY&limit=50`

### Get All Alerts

**GET** `/alerts/`

Get all alerts with optional filtering. Admin only.

**Query Parameters:** Same as Get Trip Alerts

### Get Specific Alert

**GET** `/alerts/{alert_id}`

Get details of a specific alert by ID.

### Update Alert Status

**PATCH** `/alerts/{alert_id}/status`

Update the status of an alert.

**Request Body:**

```json
"ACKNOWLEDGED"
```

### Update Alert Details

**PUT** `/alerts/{alert_id}`

Update alert details.

**Request Body:**

```json
{
  "alert_type": "WEATHER",
  "description": "Updated description",
  "status": "ACKNOWLEDGED"
}
```

### Delete Alert

**DELETE** `/alerts/{alert_id}`

Delete an alert. Admin only.

### Acknowledge Alert

**POST** `/alerts/{alert_id}/acknowledge`

Convenience endpoint to acknowledge an alert (sets status to ACKNOWLEDGED).

### Resolve Alert

**POST** `/alerts/{alert_id}/resolve`

Convenience endpoint to resolve an alert (sets status to RESOLVED).

## Permission Model

### Tourists

- Can create alerts for their own trips
- Can view alerts for their own trips

### Guides

- Can create alerts for trips they are guiding
- Can view alerts for trips they are guiding
- Can acknowledge and resolve alerts for their trips

### Admins

- Can perform all operations on all alerts
- Can access emergency alerts dashboard
- Can access alert statistics
- Can delete alerts

## Usage Scenarios

### 1. Emergency Alert Creation

When a tourist doesn't check in at expected time:

```python
# Guide or monitoring system creates emergency alert
POST /alerts/
{
  "trip_id": 123,
  "alert_type": "EMERGENCY",
  "description": "Tourist missed scheduled check-in at 14:00",
  "location": {"latitude": 28.7041, "longitude": 77.1025}
}
```

### 2. Route Deviation Detection

When automated system detects route deviation:

```python
# Automated system creates deviation alert
POST /alerts/
{
  "trip_id": 123,
  "alert_type": "DEVIATION",
  "description": "Tourist is 500m off planned route",
  "location": {"latitude": 28.7041, "longitude": 77.1025}
}
```

### 3. Emergency Dashboard Monitoring

Admin monitoring emergency situations:

```python
# Get all active emergencies
GET /alerts/emergency

# Get alert statistics for dashboard
GET /alerts/statistics
```

### 4. Guide Alert Management

Guide managing alerts for their group:

```python
# View alerts for current trip
GET /alerts/trip/123?status=NEW

# Acknowledge alert
POST /alerts/456/acknowledge

# Resolve alert after action taken
POST /alerts/456/resolve
```

## Integration with Other Systems

### Geofencing Integration

Alerts can be automatically triggered when tourists enter restricted areas:

- System detects geofence violation
- Creates DEVIATION alert automatically
- Notifies guide and admin

### Trip Tracking Integration

Alerts integrate with trip tracking system:

- Location data from tracking devices
- Automatic check-in monitoring
- Route deviation detection

### Notification System

Alerts can trigger various notifications:

- SMS to emergency contacts
- Email to guides and admins
- Push notifications to mobile apps
- Dashboard alerts

## Best Practices

1. **Immediate Emergency Response**: Emergency alerts should trigger immediate notifications
2. **Location Accuracy**: Always include accurate GPS coordinates
3. **Clear Descriptions**: Provide clear, actionable descriptions
4. **Timely Updates**: Update alert status as situations evolve
5. **Regular Monitoring**: Admins should regularly monitor emergency dashboard

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Success
- `201 Created`: Alert created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Alert not found
- `500 Internal Server Error`: Server error

Common error responses:

```json
{
  "detail": "Alert not found"
}
```

## Rate Limiting

Consider implementing rate limiting for alert creation to prevent spam:

- Max 10 alerts per user per minute
- Max 100 alerts per trip per day
- Emergency alerts have higher limits
