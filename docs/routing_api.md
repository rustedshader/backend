# Itinerary Routing API

This API provides route calculation functionality for itineraries using a self-hosted GraphHopper instance.

## Overview

The routing system calculates routes between:

- Previous day's accommodation → Current day's destination (trek start or tourist place)
- Current day's destination → Current day's accommodation

## Endpoints

### GET /routing/itinerary/{itinerary_id}

Get routes for an entire itinerary with query parameters.

**Parameters:**

- `itinerary_id` (path): ID of the itinerary
- `profile` (query): Transportation profile (`car`, `foot`, `bike`) - default: `car`
- `include_coordinates` (query): Include route coordinates - default: `true`
- `include_instructions` (query): Include turn-by-turn instructions - default: `true`

**Example:**

```bash
curl -X GET "http://localhost:8000/routing/itinerary/123?profile=car&include_coordinates=true" \
  -H "Authorization: Bearer your_token"
```

### POST /routing/itinerary/generate

Generate routes using a POST request with detailed options.

**Request Body:**

```json
{
  "itinerary_id": 123,
  "profile": "car",
  "include_coordinates": true,
  "include_instructions": true
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/routing/itinerary/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "itinerary_id": 123,
    "profile": "car",
    "include_coordinates": true,
    "include_instructions": true
  }'
```

## Response Format

```json
{
  "itinerary_id": 123,
  "total_days": 3,
  "total_distance_km": 45.67,
  "total_time_hours": 2.34,
  "profile": "car",
  "day_routes": [
    {
      "day_number": 1,
      "date": "2025-09-15",
      "day_type": "place_visit_day",
      "routes": [
        {
          "from_point": {
            "latitude": 26.166653,
            "longitude": 91.779409,
            "name": "Hotel Sunrise",
            "type": "hotel"
          },
          "to_point": {
            "latitude": 26.171218,
            "longitude": 91.83634,
            "name": "Kamakhya Temple",
            "type": "place"
          },
          "distance_meters": 8206.138,
          "distance_km": 8.21,
          "time_seconds": 584529,
          "time_minutes": 9.7,
          "time_hours": 0.16,
          "coordinates": [[91.779369, 26.166642], ...],
          "instructions": [
            {
              "distance": 252.365,
              "heading": 343.84,
              "sign": 0,
              "text": "Continue",
              "time": 18170,
              "street_name": ""
            }
          ],
          "bbox": [91.778652, 26.166642, 91.836366, 26.179465]
        }
      ],
      "total_distance_km": 8.21,
      "total_time_hours": 0.16,
      "waypoints": [...]
    }
  ]
}
```

## Transportation Profiles

- **car**: For automobile routing
- **foot**: For walking/hiking routes
- **bike**: For bicycle routing

## Prerequisites

1. **Trek Starting Coordinates**: Make sure treks have `start_latitude` and `start_longitude` set
2. **Place Coordinates**: Places need `latitude` and `longitude`
3. **Accommodation Coordinates**: Itinerary days should have `accommodation_latitude` and `accommodation_longitude`

## Route Logic

For each day, the system:

1. **Starting Point**: Previous day's accommodation (if exists)
2. **Destination**:
   - Trek days: Trek starting coordinates
   - Place visit days: Primary place coordinates
3. **End Point**: Current day's accommodation

This creates a logical flow: Hotel → Activity → Next Hotel

## Error Handling

- `404`: Itinerary not found or access denied
- `404`: No routes could be generated (missing coordinates)
- `500`: GraphHopper API error or internal server error

## GraphHopper Integration

The system uses your self-hosted GraphHopper instance at `https://maps.rustedshader.com` to calculate routes with real road data and turn-by-turn instructions.
