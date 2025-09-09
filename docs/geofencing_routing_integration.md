# Geofencing Integration with Routing API

This document explains how the geofencing system integrates with the routing API to automatically avoid restricted areas when calculating routes for itineraries.

## Overview

When the routing system calculates routes for itineraries, it now automatically:

1. **Fetches all active restricted areas** from the database
2. **Converts them to WKT POLYGON format** for GraphHopper
3. **Includes them as `block_areas`** in the routing request
4. **Ensures routes avoid these areas** automatically

## Integration Flow

### 1. Itinerary Route Generation

When you call the existing itinerary routing endpoints:

```bash
GET /routing/itinerary/{itinerary_id}
POST /routing/itinerary/generate
```

The system now automatically:

1. Calls the GraphHopper service with `include_block_areas=True`
2. Fetches active restricted areas from the geofencing system
3. Formats them as WKT POLYGON strings
4. Includes them in the GraphHopper request payload

### 2. GraphHopper Request Format

The routing service now sends requests in this format (matching your requirement):

```bash
curl --location 'https://maps.rustedshader.com/route' \
--header 'Content-Type: application/json' \
--data '{
    "profile": "car",
    "points_encoded": false,
    "points": [
      [91.779409, 26.166653],
      [91.83634, 26.171218]
    ],
    "block_areas": [
      "POLYGON((91.7500 26.1800, 91.7600 26.1800, 91.7600 26.1900, 91.7500 26.1900, 91.7500 26.1800))",
      "POLYGON((91.8000 26.1600, 91.8100 26.1600, 91.8100 26.1700, 91.8000 26.1700, 91.8000 26.1600))"
    ]
  }'
```

### 3. Automatic Restricted Area Filtering

The system only includes restricted areas that are:

- ✅ **Status**: `ACTIVE`
- ✅ **Valid From**: `NULL` or `<= NOW()`
- ✅ **Valid Until**: `NULL` or `> NOW()`
- ✅ **Boundary**: Not `NULL`
- ✅ **Ordered by**: Severity level (highest first)

## API Changes

### Updated Routing Service

The `GraphHopperService.get_route()` method now accepts:

```python
async def get_route(
    self,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    profile: str = "car",
    db: Optional[object] = None,           # NEW: Database session
    include_block_areas: bool = True,      # NEW: Include geofencing
) -> Optional[Dict[str, Any]]:
```

### Updated Itinerary Routing

The itinerary routing service now passes the database session to enable geofencing:

```python
route_data = await graphhopper_service.get_route(
    from_point.latitude,
    from_point.longitude,
    to_point.latitude,
    to_point.longitude,
    profile,
    db=db,                    # Database session for geofencing
    include_block_areas=True, # Enable restricted area avoidance
)
```

## Testing Endpoints

### Test Route with Geofencing

Test the integration with a specific route:

```bash
POST /routing-test/test-route-with-geofencing
```

**Request:**

```json
{
  "start_lat": 26.166653,
  "start_lon": 91.779409,
  "end_lat": 26.171218,
  "end_lon": 91.83634,
  "profile": "car"
}
```

**Response:**

```json
{
  "route_summary": {
    "distance_km": 15.2,
    "time_hours": 0.5,
    "geometry": {...}
  },
  "raw_route_data": {...},
  "blocked_areas_count": 3,
  "blocked_areas": [
    "POLYGON((91.7500 26.1800, 91.7600 26.1800, 91.7600 26.1900, 91.7500 26.1900, 91.7500 26.1800))"
  ],
  "request_details": {
    "start": {"latitude": 26.166653, "longitude": 91.779409},
    "end": {"latitude": 26.171218, "longitude": 91.83634},
    "profile": "car",
    "geofencing_enabled": true
  }
}
```

### Debug Active Restricted Areas

See what restricted areas are currently active:

```bash
GET /routing-test/debug/active-restricted-areas
```

**Response:**

```json
{
  "active_restricted_areas_count": 5,
  "active_restricted_areas": [
    "POLYGON((91.7500 26.1800, 91.7600 26.1800, 91.7600 26.1900, 91.7500 26.1900, 91.7500 26.1800))",
    "POLYGON((91.8000 26.1600, 91.8100 26.1600, 91.8100 26.1700, 91.8000 26.1700, 91.8000 26.1600))"
  ],
  "example_graphhopper_payload": {
    "profile": "car",
    "points_encoded": false,
    "points": [
      [91.779409, 26.166653],
      [91.83634, 26.171218]
    ],
    "block_areas": ["POLYGON((91.7500 26.1800, ...))"]
  }
}
```

## Backend Implementation Details

### Geofencing Service Function

```python
async def get_active_restricted_areas_for_routing(db: Session) -> List[str]:
    """
    Get all active restricted areas as WKT POLYGON strings for routing block_areas.
    """
    # Queries database for active areas
    # Converts PostGIS geometry to WKT format
    # Returns list of POLYGON strings for GraphHopper
```

### GraphHopper Service Integration

```python
async def get_route(..., db=None, include_block_areas=True):
    # Prepare standard routing payload
    payload = {
        "profile": profile,
        "points_encoded": False,
        "points": [[start_lon, start_lat], [end_lon, end_lat]]
    }

    # Add restricted areas if enabled
    if db and include_block_areas:
        block_areas = await self._get_active_restricted_areas(db)
        if block_areas:
            payload["block_areas"] = block_areas

    # Send POST request to GraphHopper
    async with session.post(url, json=payload) as response:
        return await response.json()
```

## Migration Required

Run the geofencing migration to create the required tables:

```bash
alembic upgrade head
```

This will create:

- `restricted_areas` table with PostGIS polygon boundaries
- `geofence_violations` table for tracking violations
- Spatial indexes for efficient geometric queries

## Coordinate Format

The system ensures coordinates are in the correct format for GraphHopper:

- **Input to Database**: `POLYGON((lon1 lat1, lon2 lat2, lon3 lat3, lon1 lat1))`
- **Output to GraphHopper**: Same WKT format
- **Coordinate Order**: Longitude first, then latitude
- **Polygon Closure**: First and last coordinates must be identical

## Example Usage

### 1. Admin Creates Restricted Area

```bash
POST /geofencing/restricted-areas
```

```json
{
  "name": "Restricted Military Zone",
  "area_type": "MILITARY_ZONE",
  "boundary_coordinates": [
    { "longitude": 91.75, "latitude": 26.18 },
    { "longitude": 91.76, "latitude": 26.18 },
    { "longitude": 91.76, "latitude": 26.19 },
    { "longitude": 91.75, "latitude": 26.19 }
  ],
  "severity_level": 5,
  "status": "ACTIVE"
}
```

### 2. System Automatically Uses Restriction

When any itinerary route is calculated:

```bash
GET /routing/itinerary/123
```

The system automatically:

1. ✅ Fetches the military zone polygon
2. ✅ Includes it in the GraphHopper request as `block_areas`
3. ✅ GraphHopper calculates routes that avoid this area
4. ✅ Returns safe routes that respect restrictions

## Benefits

1. **Automatic Safety**: Routes automatically avoid dangerous or restricted areas
2. **Real-time Updates**: New restrictions immediately affect all route calculations
3. **Flexible Control**: Admins can enable/disable restrictions without code changes
4. **Performance**: Spatial indexes ensure fast geometric queries
5. **Compliance**: Ensures tourists stay within allowed areas
6. **Transparency**: Admins can see exactly which areas are being blocked

## Configuration

The integration is enabled by default for all itinerary routing. To disable geofencing for specific routes, you can modify the service calls to use `include_block_areas=False`.

The system gracefully handles errors - if geofencing data is unavailable, routing continues without block areas rather than failing completely.
