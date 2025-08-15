# Database Schema Design (Extended)
## Collection Relationships

**Users ↔ Spots:** One-to-Many relationship via `submittedBy` field

**Spots ↔ Reviews:** One-to-Many relationship via `spotId` reference

**Users ↔ Reviews:** One-to-Many relationship via `userId` reference

**Users ↔ Favorites:** Many-to-Many relationship via separate `Favorites` collection

## Advanced Collections

### Favorites Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId (ref: Users),
  spotId: ObjectId (ref: Spots),
  createdAt: Date
}
```

### Reports Collection
```javascript
{
  _id: ObjectId,
  reportedBy: ObjectId (ref: Users),
  targetType: String, // 'spot' or 'review'
  targetId: ObjectId,
  reason: String, // 'inappropriate', 'spam', 'inaccurate', 'safety'
  description: String,
  status: String, // 'pending', 'reviewed', 'resolved'
  reviewedBy: ObjectId (ref: Users),
  resolution: String,
  createdAt: Date,
  resolvedAt: Date
}
```

### Categories Collection
```javascript
{
  _id: ObjectId,
  name: String, // 'restaurant', 'viewpoint', 'activity'
  displayName: String,
  icon: String,
  color: String,
  description: String,
  parentCategory: ObjectId (ref: Categories), // for subcategories
  isActive: Boolean
}
```

## Query Optimization

**Geospatial Queries:**
```javascript
// Find spots within 10km radius
db.spots.find({
  location: {
    $near: {
      $geometry: { type: \"Point\", coordinates: [-123.1207, 49.2827] },
      $maxDistance: 10000
    }
  }
})
```

**Compound Indexes:**
```javascript
// Optimized for filtered location searches
db.spots.createIndex({ 
  \"location\": \"2dsphere\", 
  \"category\": 1, 
  \"averageRating\": -1 
})

// User activity optimization
db.reviews.createIndex({ 
  \"userId\": 1, 
  \"createdAt\": -1 
})
```

## Data Validation Rules

**Spot Validation:**
- Name: 3-100 characters, required
- Coordinates: Valid latitude/longitude within bounds
- Category: Must exist in Categories collection
- Rating: 1-5 decimal value

**Review Validation:**
- Rating: Integer 1-5, required
- Content: 10-2000 characters
- One review per user per spot

## Backup & Recovery

**Backup Strategy:**
- Daily automated backups via MongoDB Atlas
- Point-in-time recovery available
- Cross-region backup replication

**Data Retention:**
- User data: Retained until account deletion
- Soft delete for spots/reviews (flagged, not removed)
- Analytics data: 2-year retention period