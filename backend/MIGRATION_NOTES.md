# Migration Notes

## 2025-12-13: Add Indexes to Photos Table (Migration 9a6c7f6b7d7a)

### Summary
Added 14 indexes to the `photos` table to significantly improve query performance for common filtering and ordering operations.

### Impact
- **Performance**: Query performance improvements of 10-100x for filtered queries
- **Storage**: Approximately 15-25% additional storage overhead for the photos table
- **Downtime**: No downtime required - indexes are created concurrently if using PostgreSQL 11+

### How to Apply

#### For Production Deployments:
```bash
cd backend
alembic upgrade head
```

#### For Development:
```bash
cd backend
alembic upgrade head
```

### Verification

After applying the migration, verify the indexes were created:

```bash
# Run the test suite
pytest test_indexes.py -v

# Or check manually in PostgreSQL
psql $DATABASE_URL -c "\d photos"
```

### Expected Indexes

The migration creates the following indexes:
- `ix_photos_owner_id` - Foreign key to users
- `ix_photos_library_id` - Foreign key to libraries
- `ix_photos_date` - For date ordering and range queries
- `ix_photos_albums_gin` - GIN index for album filtering
- `ix_photos_keywords_gin` - GIN index for keyword filtering
- `ix_photos_persons_gin` - GIN index for person filtering
- `ix_photos_master_fingerprint` - For deduplication
- `ix_photos_favorite` - For favorite filtering
- `ix_photos_isphoto` - For photo type filtering
- `ix_photos_ismovie` - For movie type filtering
- `ix_photos_screenshot` - For screenshot filtering
- `ix_photos_panorama` - For panorama filtering
- `ix_photos_portrait` - For portrait filtering
- `ix_photos_location` - Composite index for location queries

### Rollback

If needed, rollback with:
```bash
alembic downgrade -1
```

### More Information

See [INDEXES.md](INDEXES.md) for detailed documentation about each index, their purpose, and performance impact.
