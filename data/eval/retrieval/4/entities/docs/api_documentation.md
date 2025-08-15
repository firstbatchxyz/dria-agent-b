# API Documentation
## Base Configuration

**Base URL:** `https://api.kankun.app/v1`

**Authentication:** Bearer token (JWT)

**Content Type:** `application/json`

**Rate Limiting:** 1000 requests/hour for authenticated users, 100/hour for anonymous

## Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  \"email\": \"user@example.com\",
  \"username\": \"johndoe\",
  \"password\": \"SecurePassword123\",
  \"firstName\": \"John\",
  \"lastName\": \"Doe\"
}
```

**Response (201):**
```json
{
  \"success\": true,
  \"data\": {
    \"user\": {
      \"id\": \"507f1f77bcf86cd799439011\",
      \"email\": \"user@example.com\",
      \"username\": \"johndoe\"
    },
    \"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\"
  }
}
```

### POST /auth/login
Authenticate existing user.

**Request Body:**
```json
{
  \"email\": \"user@example.com\",
  \"password\": \"SecurePassword123\"
}
```

**Response (200):**
```json
{
  \"success\": true,
  \"data\": {
    \"user\": {
      \"id\": \"507f1f77bcf86cd799439011\",
      \"email\": \"user@example.com\",
      \"username\": \"johndoe\",
      \"profile\": {
        \"firstName\": \"John\",
        \"lastName\": \"Doe\",
        \"avatar\": \"https://cdn.kankun.app/avatars/johndoe.jpg\"
      }
    },
    \"token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\"
  }
}
```

## Spots Endpoints

### GET /spots
Search and discover spots with filtering options.

**Query Parameters:**
- `lat` (required): Latitude for location-based search
- `lng` (required): Longitude for location-based search
- `radius`: Search radius in kilometers (default: 10)
- `category`: Filter by spot category
- `minRating`: Minimum average rating (1-5)
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset

**Response (200):**
```json
{
  \"success\": true,
  \"data\": {
    \"spots\": [
      {
        \"id\": \"507f1f77bcf86cd799439012\",
        \"name\": \"Hidden Waterfall Trail\",
        \"description\": \"A secluded waterfall accessible via a 20-minute hike\",
        \"category\": \"nature\",
        \"location\": {
          \"coordinates\": [-123.1207, 49.2827],
          \"address\": \"North Shore Mountains, Vancouver, BC\",
          \"city\": \"Vancouver\",
          \"country\": \"Canada\"
        },
        \"averageRating\": 4.7,
        \"reviewCount\": 23,
        \"images\": [
          \"https://cdn.kankun.app/spots/waterfall-1.jpg\"
        ],
        \"distance\": 2.3,
        \"submittedBy\": {
          \"username\": \"nature_lover\",
          \"avatar\": \"https://cdn.kankun.app/avatars/nature_lover.jpg\"
        }
      }
    ],
    \"pagination\": {
      \"total\": 157,
      \"limit\": 20,
      \"offset\": 0,
      \"hasNext\": true
    }
  }
}
```

### POST /spots
Submit a new hidden spot (requires authentication).

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  \"name\": \"Secret Rooftop Garden\",
  \"description\": \"Amazing city views from this hidden rooftop garden\",
  \"category\": \"viewpoint\",
  \"location\": {
    \"coordinates\": [-74.0059, 40.7128],
    \"address\": \"Manhattan, NY\",
    \"city\": \"New York\",
    \"country\": \"USA\"
  },
  \"tags\": [\"views\", \"photography\", \"sunset\"],
  \"difficulty\": \"easy\",
  \"bestTimeToVisit\": \"sunset\",
  \"estimatedDuration\": 45
}
```

**Response (201):**
```json
{
  \"success\": true,
  \"data\": {
    \"spot\": {
      \"id\": \"507f1f77bcf86cd799439013\",
      \"name\": \"Secret Rooftop Garden\",
      \"isVerified\": false,
      \"createdAt\": \"2024-01-15T10:30:00Z\"
    }
  }
}
```

## Reviews Endpoints

### GET /spots/:spotId/reviews
Get reviews for a specific spot.

**Response (200):**
```json
{
  \"success\": true,
  \"data\": {
    \"reviews\": [
      {
        \"id\": \"507f1f77bcf86cd799439014\",
        \"rating\": 5,
        \"title\": \"Absolutely breathtaking!\",
        \"content\": \"This place exceeded all expectations...\",
        \"visitDate\": \"2024-01-10\",
        \"user\": {
          \"username\": \"adventure_seeker\",
          \"avatar\": \"https://cdn.kankun.app/avatars/adventure_seeker.jpg\"
        },
        \"helpful\": {
          \"upvotes\": 12,
          \"downvotes\": 1
        },
        \"createdAt\": \"2024-01-12T15:45:00Z\"
      }
    ]
  }
}
```

### POST /spots/:spotId/reviews
Submit a review for a spot (requires authentication).

**Request Body:**
```json
{
  \"rating\": 4,
  \"title\": \"Great hidden gem\",
  \"content\": \"Really enjoyed this spot, perfect for photography\",
  \"visitDate\": \"2024-01-10\"
}
```

## Error Responses

**Standard Error Format:**
```json
{
  \"success\": false,
  \"error\": {
    \"code\": \"VALIDATION_ERROR\",
    \"message\": \"Invalid request parameters\",
    \"details\": [
      {
        \"field\": \"email\",
        \"message\": \"Email is required\"
      }
    ]
  }
}
```

**Common HTTP Status Codes:**
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

---

