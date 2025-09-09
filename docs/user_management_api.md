# User Management API Documentation

## Overview

This document describes the comprehensive User Management API endpoints for administrators to manage users in the tourism safety platform.

## Base URL

All user management endpoints are prefixed with `/users` and require admin authentication.

## Authentication

All endpoints require admin-level authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <admin_jwt_token>
```

## Endpoints

### 1. List All Users

**GET** `/users/admin`

Lists all users in the system with optional filtering and pagination.

**Query Parameters:**

- `role_filter` (optional): Filter by user role (`admin`, `tourist`, `guide`, `super_admin`)
- `is_active_filter` (optional): Filter by active status (`true`/`false`)
- `is_verified_filter` (optional): Filter by verification status (`true`/`false`)
- `limit` (optional): Maximum number of results (1-1000, default: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**

```json
{
  "users": [
    {
      "id": 1,
      "first_name": "John",
      "middle_name": null,
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "country_code": "US",
      "phone_number": "+1234567890",
      "indian_citizenship": false,
      "is_kyc_verified": true,
      "is_email_verified": true,
      "is_active": true,
      "role": "tourist",
      "blockchain_address": "0x123...",
      "tourist_id_token": 12345,
      "tourist_id_transaction_hash": "0xabc..."
    }
  ],
  "total_count": 150,
  "offset": 0,
  "limit": 100
}
```

### 2. Get User Information by ID

**GET** `/users/admin/{user_id}`

Retrieves detailed information about a specific user.

**Path Parameters:**

- `user_id` (required): The unique user ID

**Response:**

```json
{
  "id": 1,
  "first_name": "John",
  "middle_name": null,
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "country_code": "US",
  "phone_number": "+1234567890",
  "indian_citizenship": false,
  "is_kyc_verified": true,
  "is_email_verified": true,
  "is_active": true,
  "role": "tourist",
  "blockchain_address": "0x123...",
  "tourist_id_token": 12345,
  "tourist_id_transaction_hash": "0xabc..."
}
```

### 3. Verify User

**POST** `/users/admin/{user_id}/verify`

Manually verify a user's KYC status after document review.

**Path Parameters:**

- `user_id` (required): The unique user ID

**Request Body:**

```json
{
  "verification_notes": "Documents verified manually at entry point"
}
```

**Response:**

```json
{
  "success": true,
  "message": "User 1 has been successfully verified",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "is_kyc_verified": true
    // ... other user fields
  }
}
```

### 4. Get User Blockchain ID Information

**GET** `/users/admin/{user_id}/blockchain-id`

Retrieves blockchain-related information for a specific user.

**Path Parameters:**

- `user_id` (required): The unique user ID

**Response:**

```json
{
  "user_id": 1,
  "blockchain_address": "0x123...",
  "tourist_id_token": 12345,
  "tourist_id_transaction_hash": "0xabc...",
  "has_blockchain_id": true,
  "is_kyc_verified": true
}
```

### 5. Issue Blockchain ID to User

**POST** `/users/admin/{user_id}/blockchain-id`

Issues a blockchain ID to a verified user with an approved itinerary.

**Path Parameters:**

- `user_id` (required): The unique user ID

**Request Body:**

```json
{
  "user_id": 1,
  "itinerary_id": 5,
  "validity_days": 30
}
```

**Response:**

```json
{
  "success": true,
  "message": "Blockchain ID issued successfully",
  "tourist_id_token": 12345,
  "blockchain_address": "0x123...",
  "transaction_hash": "0xabc...",
  "blockchain_private_key": "0xdef...",
  "validity_days": 30
}
```

## Additional Convenience Endpoints

### 6. Get User Statistics

**GET** `/users/admin/stats`

Returns comprehensive user statistics for admin dashboard.

**Response:**

```json
{
  "total_users": 150,
  "by_role": {
    "admin": 5,
    "tourist": 120,
    "guide": 20,
    "super_admin": 5
  },
  "by_verification": {
    "verified": 100,
    "unverified": 50
  },
  "by_status": {
    "active": 140,
    "inactive": 10
  },
  "blockchain_ids_issued": 80
}
```

### 7. Update User Status

**PUT** `/users/admin/{user_id}/status`

Updates a user's active/inactive status.

**Request Body:**

```json
{
  "is_active": false,
  "reason": "Suspicious activity detected"
}
```

### 8. Get Unverified Users

**GET** `/users/admin/unverified`

Convenience endpoint to get only unverified users.

### 9. Get Users Without Blockchain ID

**GET** `/users/admin/no-blockchain-id`

Gets verified users who don't have blockchain IDs yet.

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions (non-admin user)
- `404 Not Found`: User not found
- `500 Internal Server Error`: Server error

Error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Usage Examples

### Example 1: List all unverified tourists

```bash
curl -X GET "/users/admin?role_filter=tourist&is_verified_filter=false" \
  -H "Authorization: Bearer <admin_token>"
```

### Example 2: Verify a user

```bash
curl -X POST "/users/admin/123/verify" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"verification_notes": "Documents verified at border checkpoint"}'
```

### Example 3: Issue blockchain ID

```bash
curl -X POST "/users/admin/123/blockchain-id" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "itinerary_id": 456, "validity_days": 30}'
```

## Security Notes

1. All endpoints require admin authentication
2. User verification should only be done after proper document review
3. Blockchain ID issuance requires the user to be KYC verified
4. User status changes are logged for audit purposes
5. Sensitive information like blockchain private keys should be handled securely

## Related Endpoints

- Authentication: `/auth/*`
- Admin-specific: `/admin/*`
- Geofencing: `/geofencing/*`
- Itinerary Management: `/itinerary/*`
