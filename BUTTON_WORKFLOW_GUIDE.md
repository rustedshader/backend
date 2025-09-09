# 🎯 **Button-Driven Trip Tracking Workflow**

## 📱 **User Interface Flow**

### **🏨 TOUR DAY WORKFLOW**

```
[START DAY] → [GPS Tracking] → [VISITING] → [RETURN TO HOTEL] → [GPS Tracking] → [COMPLETED]
```

#### **Step 1: Start Day**

**Button**: `🟢 START DAY`
**API**: `POST /trip/{trip_id}/start-day`

```json
{
  "trip_type": "tour_day",
  "hotel_lat": 28.6139,
  "hotel_lon": 77.209,
  "hotel_name": "Hotel Taj Palace",
  "destination_lat": 28.6562,
  "destination_lon": 77.241,
  "destination_name": "Red Fort"
}
```

**Response**: Route from hotel to destination
**Status**: `assigned` → `started`
**Phase**: `to_destination`

#### **Step 2: Continuous GPS Tracking**

**API**: `POST /trip/{trip_id}/live-location` (every 30 seconds)

```json
{
  "latitude": 28.62,
  "longitude": 77.22,
  "timestamp": 1694234567,
  "source": "mobile_gps",
  "accuracy": 5.0,
  "speed": 2.5,
  "battery_level": 85
}
```

#### **Step 3: Reach Destination**

**Button**: `🟡 VISITING`
**API**: `POST /trip/{trip_id}/visiting`
**Status**: `started` → `visiting`
**Phase**: `at_destination`

#### **Step 4: Return to Hotel**

**Button**: `🏨 RETURN TO HOTEL`
**API**: `POST /trip/{trip_id}/return-to-hotel`

```json
{
  "current_lat": 28.6562,
  "current_lon": 77.241
}
```

**Response**: Route back to hotel
**Status**: `visiting` → `returning`
**Phase**: `to_hotel`

#### **Step 5: Continue GPS Tracking Until Hotel**

Same live location API, system auto-completes when back at hotel.

---

### **🥾 TREK DAY WORKFLOW**

```
[START DAY] → [GPS to Trek] → [LINK DEVICE] → [START TREK] → [Device Tracking] → [END TREK] → [GPS to Hotel] → [COMPLETED]
```

#### **Step 1: Start Day**

**Button**: `🟢 START DAY`
**API**: `POST /trip/{trip_id}/start-day`

```json
{
  "trip_type": "trek_day",
  "hotel_lat": 28.6139,
  "hotel_lon": 77.209,
  "hotel_name": "Mountain Lodge",
  "destination_lat": 28.238,
  "destination_lon": 83.993,
  "destination_name": "Annapurna Base Camp Trek"
}
```

**Response**: Route from hotel to trek starting point
**Status**: `assigned` → `started`
**Phase**: `to_trek_start`

#### **Step 2: GPS Tracking to Trek Start**

**API**: `POST /trip/{trip_id}/live-location` (continuous)
Mobile phone sends GPS data while traveling to trek start.

#### **Step 3: Link Tracking Device**

**Button**: `🔗 LINK DEVICE`
**API**: `POST /trip/{trip_id}/link-device`

```json
{
  "device_id": "GPS_TRACKER_001"
}
```

**Response**: Device linked confirmation

#### **Step 4: Start Trek**

**Button**: `🥾 START TREK`
**API**: `POST /trip/{trip_id}/start-trek`

```json
{
  "device_id": "GPS_TRACKER_001"
}
```

**Response**: Offline trek data downloaded
**Status**: `started` → `visiting`
**Phase**: `trek_active`

#### **Step 5: Download Offline Trek Data**

**API**: `GET /trip/{trip_id}/trek-data`

```json
{
  "trek_id": 123,
  "path_data": {
    "waypoints": [...],
    "total_distance_meters": 15000,
    "estimated_duration_hours": 8,
    "safety_notes": "Watch for weather changes"
  },
  "offline_ready": true
}
```

#### **Step 6: Tracking Device Sends Data**

**API**: `POST /trip/{trip_id}/live-location` (from tracking device)

```json
{
  "latitude": 28.24,
  "longitude": 83.995,
  "timestamp": 1694234567,
  "source": "tracking_device",
  "device_id": "GPS_TRACKER_001"
}
```

Phone goes offline, tracking device continues sending location data.

#### **Step 7: End Trek**

**Button**: `🏁 END TREK`
**API**: `POST /trip/{trip_id}/end-trek`

```json
{
  "trek_end_lat": 28.245,
  "trek_end_lon": 83.998
}
```

**Response**: Route from trek end back to hotel
**Status**: `visiting` → `returning`
**Phase**: `from_trek_end`

#### **Step 8: GPS Tracking Back to Hotel**

**API**: `POST /trip/{trip_id}/live-location` (mobile phone resumes)
Mobile phone resumes GPS tracking for return journey.

---

## 🗄️ **Database Schema Updates**

### **Enhanced Trips Table**

```sql
ALTER TABLE trips ADD COLUMN trip_type VARCHAR(20);
ALTER TABLE trips ADD COLUMN current_phase VARCHAR(30);
ALTER TABLE trips ADD COLUMN hotel_latitude FLOAT;
ALTER TABLE trips ADD COLUMN hotel_longitude FLOAT;
ALTER TABLE trips ADD COLUMN hotel_name VARCHAR(255);
ALTER TABLE trips ADD COLUMN destination_latitude FLOAT;
ALTER TABLE trips ADD COLUMN destination_longitude FLOAT;
ALTER TABLE trips ADD COLUMN destination_name VARCHAR(255);
ALTER TABLE trips ADD COLUMN trek_start_latitude FLOAT;
ALTER TABLE trips ADD COLUMN trek_start_longitude FLOAT;
ALTER TABLE trips ADD COLUMN trek_end_latitude FLOAT;
ALTER TABLE trips ADD COLUMN trek_end_longitude FLOAT;
ALTER TABLE trips ADD COLUMN linked_device_id VARCHAR(100);
ALTER TABLE trips ADD COLUMN device_linked_at TIMESTAMP;
ALTER TABLE trips ADD COLUMN tracking_started_at TIMESTAMP;
ALTER TABLE trips ADD COLUMN tracking_ended_at TIMESTAMP;
ALTER TABLE trips ADD COLUMN is_tracking_active BOOLEAN DEFAULT FALSE;
```

### **Enhanced LocationHistory Table**

```sql
ALTER TABLE location_history ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE location_history ADD COLUMN latitude FLOAT NOT NULL;
ALTER TABLE location_history ADD COLUMN longitude FLOAT NOT NULL;
ALTER TABLE location_history ADD COLUMN altitude FLOAT;
ALTER TABLE location_history ADD COLUMN accuracy FLOAT;
ALTER TABLE location_history ADD COLUMN speed FLOAT;
ALTER TABLE location_history ADD COLUMN bearing FLOAT;
ALTER TABLE location_history ADD COLUMN source VARCHAR(20);
ALTER TABLE location_history ADD COLUMN trip_phase VARCHAR(30);
ALTER TABLE location_history ADD COLUMN device_id VARCHAR(100);
ALTER TABLE location_history ADD COLUMN battery_level INTEGER;
ALTER TABLE location_history ADD COLUMN signal_strength INTEGER;
ALTER TABLE location_history ADD COLUMN notes TEXT;
ALTER TABLE location_history ADD COLUMN is_waypoint BOOLEAN DEFAULT FALSE;
```

### **New TrekPath Table**

```sql
CREATE TABLE trek_paths (
    id SERIAL PRIMARY KEY,
    trek_id INTEGER REFERENCES treks(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    path_coordinates GEOMETRY(LINESTRING, 4326),
    total_distance_meters FLOAT,
    estimated_duration_hours FLOAT,
    elevation_gain_meters FLOAT,
    difficulty_rating INTEGER,
    waypoints TEXT, -- JSON string
    safety_notes TEXT,
    created_at BIGINT,
    is_active BOOLEAN DEFAULT TRUE
);
```

### **New RouteSegment Table**

```sql
CREATE TABLE route_segments (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER REFERENCES trips(id),
    segment_type VARCHAR(50),
    start_timestamp BIGINT,
    end_timestamp BIGINT,
    start_latitude FLOAT,
    start_longitude FLOAT,
    end_latitude FLOAT,
    end_longitude FLOAT,
    total_distance_meters FLOAT,
    total_duration_seconds INTEGER,
    max_speed_ms FLOAT,
    avg_speed_ms FLOAT,
    trek_path_id INTEGER REFERENCES trek_paths(id),
    is_completed BOOLEAN DEFAULT FALSE,
    notes TEXT
);
```

---

## 📊 **Status & Phase Management**

### **Trip Status Values**

- `assigned`: Trip created, not started
- `started`: Day started, traveling to destination
- `visiting`: At destination (tourist location or trekking)
- `returning`: Coming back to hotel
- `completed`: Day completed successfully
- `cancelled`: Trip cancelled

### **Tour Day Phases**

- `to_destination`: Mobile GPS from hotel to tourist location
- `at_destination`: At tourist location
- `to_hotel`: Mobile GPS from tourist location back to hotel

### **Trek Day Phases**

- `to_trek_start`: Mobile GPS from hotel to trek starting point
- `trek_active`: Tracking device during actual trek
- `from_trek_end`: Mobile GPS from trek end back to hotel

---

## 🔄 **API Integration Summary**

### **Required Mobile App Screens**

1. **Trip Dashboard**: Shows current status and available buttons
2. **GPS Tracking Screen**: Real-time location updates
3. **Device Linking Screen**: For trek days only
4. **Offline Trek Map**: Downloaded trek data for offline use
5. **Return Route Screen**: Navigation back to hotel

### **Background Services**

1. **Location Service**: Sends GPS data every 30 seconds
2. **Battery Monitor**: Tracks device battery levels
3. **Network Monitor**: Handles offline/online status
4. **Emergency Service**: Quick emergency alerts

This system provides complete visibility and control over tourist movements while maintaining safety and providing valuable analytics! 🎯
