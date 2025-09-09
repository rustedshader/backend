# JWT Refresh Token Implementation

## 🎯 Overview

The refresh token system provides a secure way to maintain user sessions without requiring frequent re-authentication. This implementation follows industry best practices for JWT token management.

## 🔑 Token Specifications

### Access Token

- **Lifetime**: 1 hour (3600 seconds)
- **Purpose**: API authentication
- **Storage**: Client-side (memory/localStorage)
- **Refresh**: Using refresh token when expired

### Refresh Token

- **Lifetime**: 1 day (86400 seconds)
- **Purpose**: Generate new access tokens
- **Storage**: Database with revocation support
- **Security**: Can be revoked on logout

## 🔄 Authentication Workflow

### Initial Login

```mermaid
sequenceDiagram
    Client->>Server: POST /auth/login (credentials)
    Server->>Database: Validate user
    Database-->>Server: User data
    Server->>Database: Store refresh token
    Server-->>Client: access_token + refresh_token
```

### Token Refresh

```mermaid
sequenceDiagram
    Client->>Server: POST /auth/refresh (refresh_token)
    Server->>Database: Validate refresh token
    Database-->>Server: Token valid
    Server-->>Client: new access_token
```

### Logout

```mermaid
sequenceDiagram
    Client->>Server: POST /auth/logout (refresh_token)
    Server->>Database: Revoke refresh token
    Database-->>Server: Token revoked
    Server-->>Client: Logout confirmation
```

## 📚 API Endpoints

### 1. Login

**POST** `/auth/login`

Get initial access and refresh tokens.

**Request:**

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secret123
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Refresh Token

**POST** `/auth/refresh`

Get a new access token using refresh token.

**Request:**

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Logout

**POST** `/auth/logout`

Revoke refresh token to logout.

**Request:**

```http
POST /auth/logout
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**

```json
{
  "message": "Successfully logged out"
}
```

## 🛡️ Security Features

### Token Validation

- **JWT Signature Verification**: All tokens signed with secret key
- **Expiry Checking**: Both access and refresh tokens have expiration
- **Database Validation**: Refresh tokens verified against database
- **Revocation Support**: Tokens can be invalidated immediately

### Attack Prevention

- **Token Replay Protection**: Revoked tokens cannot be reused
- **Secure Storage**: Refresh tokens stored with revocation flag
- **Automatic Cleanup**: Expired tokens marked as invalid
- **Role-Based Access**: Tokens include user role information

## 💾 Database Schema

### RefreshToken Model

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token VARCHAR UNIQUE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

## 🔧 Implementation Details

### Token Creation

```python
# Access token (short-lived)
access_token = create_access_token(
    data={"sub": user.email, "role": user.role.value},
    expires_delta=3600  # 1 hour
)

# Refresh token (long-lived)
refresh_token = create_refresh_token(
    data={"sub": user.email, "role": user.role.value},
    expires_delta=86400  # 1 day
)
```

### Token Validation

```python
async def validate_refresh_token(db: Session, refresh_token: str) -> dict | None:
    # 1. Decode JWT and check expiry
    payload = decode_token(refresh_token)
    if not payload:
        return None

    # 2. Check database for revocation
    db_token = db.exec(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            ~RefreshToken.is_revoked
        )
    ).first()

    # 3. Verify not expired in database
    if db_token and db_token.expires_at > current_timestamp:
        return payload

    return None
```

## 📱 Client Implementation

### JavaScript Example

```javascript
class AuthManager {
  constructor() {
    this.accessToken = localStorage.getItem("access_token");
    this.refreshToken = localStorage.getItem("refresh_token");
  }

  async login(username, password) {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: `username=${username}&password=${password}`,
    });

    if (response.ok) {
      const tokens = await response.json();
      this.accessToken = tokens.access_token;
      this.refreshToken = tokens.refresh_token;

      localStorage.setItem("access_token", this.accessToken);
      localStorage.setItem("refresh_token", this.refreshToken);
    }
  }

  async refreshAccessToken() {
    const response = await fetch("/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      localStorage.setItem("access_token", this.accessToken);
      return true;
    }

    return false;
  }

  async apiCall(url, options = {}) {
    // Add access token to request
    const headers = {
      Authorization: `Bearer ${this.accessToken}`,
      ...options.headers,
    };

    let response = await fetch(url, { ...options, headers });

    // If token expired, try to refresh
    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        // Retry with new token
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        response = await fetch(url, { ...options, headers });
      }
    }

    return response;
  }

  async logout() {
    await fetch("/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }
}
```

## 🧪 Testing

### Test Scenarios

1. **Login Flow**: Verify tokens are issued correctly
2. **Token Refresh**: Verify new access tokens are generated
3. **Token Expiry**: Verify expired tokens are rejected
4. **Token Revocation**: Verify logout invalidates tokens
5. **Invalid Tokens**: Verify malformed tokens are rejected

### Test Commands

```bash
# Start server
uvicorn app.main:app --reload

# Run refresh token tests
python test_refresh_token_complete.py

# Manual testing with curl
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass"

curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your.refresh.token"}'
```

## 🚀 Deployment Considerations

### Production Settings

- **Secret Key**: Use strong, unique JWT secret key
- **HTTPS Only**: Never send tokens over HTTP
- **Token Storage**: Consider secure storage options
- **Monitoring**: Log token usage and failures

### Environment Variables

```bash
# Required for JWT tokens
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256

# Database connection
DATABASE_URL=postgresql://user:pass@localhost/db
```

## 📈 Performance Optimization

### Database Indexes

- ✅ `refresh_tokens(token)` - Fast token lookup
- ✅ `refresh_tokens(user_id)` - User token queries
- ✅ `refresh_tokens(expires_at)` - Cleanup queries

### Cleanup Strategy

```python
# Periodic cleanup of expired tokens
async def cleanup_expired_tokens(db: Session):
    current_time = int(datetime.utcnow().timestamp())

    # Delete expired tokens
    statement = delete(RefreshToken).where(
        RefreshToken.expires_at < current_time
    )

    db.exec(statement)
    db.commit()
```

## ✅ Security Checklist

- ✅ JWT tokens signed with secret key
- ✅ Access tokens have short expiry (1 hour)
- ✅ Refresh tokens stored in database
- ✅ Token revocation on logout
- ✅ Expired token cleanup
- ✅ Input validation on all endpoints
- ✅ Error handling for edge cases
- ✅ Protection against token replay
- ✅ Role-based access control

## 🎉 Benefits

### For Users

- **Seamless Experience**: No frequent login prompts
- **Security**: Tokens can be revoked if compromised
- **Multi-Device**: Can logout from all devices

### For Developers

- **Scalable**: Stateless access token validation
- **Flexible**: Fine-grained control over sessions
- **Standard**: Industry-standard JWT implementation

The refresh token system is now **production-ready** and provides robust session management for the SIH tourism platform! 🚀
