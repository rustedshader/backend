# Geofencing API Documentation

This API provides endpoints for managing restricted areas and geofence violations for tourist safety and compliance.

## Overview

The Geofencing system allows administrators to:

- Define polygon-based restricted areas on a map
- Set different types of restrictions (danger zones, private property, military zones, etc.)
- Monitor when tourists enter or approach restricted areas
- Automatically log violations and send notifications

## Key Features

- **Polygon-based boundaries**: Use multiple coordinate points to define complex area shapes
- **Real-time location checking**: Check if coordinates are within restricted areas
- **Automatic violation logging**: Track when users enter restricted zones
- **Flexible area types**: Support for different restriction categories
- **Warning zones**: Configurable buffer distances for approach warnings
- **Admin management**: Full CRUD operations for area management

## Endpoints

### Admin Endpoints (Requires Admin Authentication)

#### Create Restricted Area

```
POST /geofencing/restricted-areas
```

Create a new restricted area with polygon boundaries.

**Request Body Example:**

```json
{
  "name": "Protected Wildlife Reserve",
  "description": "Protected area for endangered species habitat",
  "area_type": "PROTECTED_AREA",
  "boundary_coordinates": [
    { "longitude": 77.1234, "latitude": 28.5678 },
    { "longitude": 77.1345, "latitude": 28.5678 },
    { "longitude": 77.1345, "latitude": 28.5789 },
    { "longitude": 77.1234, "latitude": 28.5789 }
  ],
  "severity_level": 3,
  "restriction_reason": "Wildlife protection during breeding season",
  "contact_info": "Forest Department: +91-123-456-7890",
  "send_warning_notification": true,
  "auto_alert_authorities": false,
  "buffer_distance_meters": 200
}
```

#### Get All Restricted Areas

```
GET /geofencing/restricted-areas?status_filter=active&area_type_filter=DANGER_ZONE&limit=50&offset=0
```

#### Get Specific Restricted Area

```
GET /geofencing/restricted-areas/{area_id}
```

#### Update Restricted Area

```
PUT /geofencing/restricted-areas/{area_id}
```

#### Delete Restricted Area

```
DELETE /geofencing/restricted-areas/{area_id}
```

#### Get Area Types and Status Types

```
GET /geofencing/admin/area-types
GET /geofencing/admin/status-types
```

### User Endpoints (Requires User Authentication)

#### Check Location Restrictions

```
POST /geofencing/check-location
```

**Request Body:**

```json
{
  "longitude": 77.125,
  "latitude": 28.57,
  "user_id": 123
}
```

**Response Example:**

```json
{
  "is_restricted": true,
  "restricted_areas": [
    {
      "id": 1,
      "name": "Protected Wildlife Reserve",
      "area_type": "PROTECTED_AREA",
      "status": "ACTIVE",
      "severity_level": 3,
      "created_at": "2025-09-10T10:30:00Z"
    }
  ],
  "warnings": [
    "You are currently in a restricted protected area: Protected Wildlife Reserve"
  ],
  "severity_level": 3
}
```

#### Check Coordinates (Alternative)

```
GET /geofencing/check-location/{longitude}/{latitude}?log_violations=true
```

### Public Endpoints (No Authentication Required)

#### Get Public Restricted Areas

```
GET /geofencing/public/restricted-areas?area_type_filter=DANGER_ZONE&limit=50
```

Returns basic information about active restricted areas without detailed coordinates.

## Area Types

- **RESTRICTED_ZONE**: General restricted area where access is limited
- **DANGER_ZONE**: Area with potential safety hazards
- **PRIVATE_PROPERTY**: Private property where trespassing is prohibited
- **PROTECTED_AREA**: Environmentally protected area with access restrictions
- **MILITARY_ZONE**: Military installation or security-sensitive area
- **SEASONAL_CLOSURE**: Area closed during specific seasons or periods

## Status Types

- **ACTIVE**: Area restriction is currently active and enforced
- **INACTIVE**: Area restriction is not currently active
- **TEMPORARILY_DISABLED**: Area restriction is temporarily disabled for maintenance

## Frontend Integration

### Creating Restricted Areas

1. **Map Interface**: Use a mapping library (like Leaflet, Google Maps, or Mapbox) to allow admins to draw polygons
2. **Coordinate Collection**: Collect the polygon vertices as longitude/latitude pairs
3. **Form Submission**: Send the coordinates along with area details to the create endpoint

**Example JavaScript (using Leaflet):**

```javascript
// Initialize map
const map = L.map("map").setView([28.5678, 77.1234], 13);

// Add drawing controls
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const drawControl = new L.Control.Draw({
  edit: {
    featureGroup: drawnItems,
  },
  draw: {
    polygon: true,
    polyline: false,
    rectangle: true,
    circle: false,
    marker: false,
  },
});
map.addControl(drawControl);

// Handle polygon creation
map.on(L.Draw.Event.CREATED, function (e) {
  const layer = e.layer;
  const coordinates = layer.getLatLngs()[0].map((latlng) => ({
    longitude: latlng.lng,
    latitude: latlng.lat,
  }));

  // Send coordinates to backend
  createRestrictedArea({
    name: "New Restricted Area",
    area_type: "RESTRICTED_ZONE",
    boundary_coordinates: coordinates,
    // ... other fields
  });
});
```

### Real-time Location Checking

```javascript
// Get user's current location
navigator.geolocation.getCurrentPosition(async (position) => {
  const { longitude, latitude } = position.coords;

  // Check if location is restricted
  const response = await fetch(
    `/geofencing/check-location/${longitude}/${latitude}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  const result = await response.json();

  if (result.is_restricted) {
    // Show warning to user
    alert(`Warning: ${result.warnings.join(", ")}`);
  }
});
```

## Database Schema

### restricted_areas Table

- Stores polygon boundaries using PostGIS geometry
- Includes administrative details and enforcement settings
- Supports temporal restrictions (valid_from, valid_until)

### geofence_violations Table

- Logs when users enter or approach restricted areas
- Stores exact violation location and timestamp
- Tracks notification and response status

## Security Considerations

1. **Admin-only Management**: Only authenticated admin users can create/modify restricted areas
2. **Coordinate Validation**: All coordinates are validated for proper ranges
3. **Rate Limiting**: Consider implementing rate limiting for location check endpoints
4. **Audit Trail**: All violations are logged with user and timestamp information

## Performance Notes

- Uses PostGIS spatial indexes for efficient geometric queries
- Supports batch location checking for multiple points
- Configurable result limits to prevent large response payloads
- Optimized queries using spatial containment and distance functions
