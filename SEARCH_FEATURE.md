# Advanced Search Feature

## Overview

PhotoSafe now includes an advanced search feature that allows you to search through your photo collection using multiple criteria simultaneously. The search is powered by a dedicated `search_data` table that indexes searchable metadata for fast and efficient queries.

## Features

- **Multi-select filters**: Choose multiple values for each filter category
- **Multiple filter categories**: Combine different types of filters (places, labels, keywords, etc.)
- **Text search**: Search in photo titles and descriptions
- **Date range filtering**: Limit results to specific time periods
- **Logical operators**: 
  - Within a category: OR logic (e.g., "Paris OR London")
  - Between categories: AND logic (e.g., "in Paris" AND "has Sunset label")

## Searchable Metadata

The search feature indexes the following metadata from photos:

- **Places**: Locations from photo metadata (name, city, state, country)
- **Labels**: Visual labels detected or assigned to photos
- **Keywords**: Keywords and tags associated with photos
- **Persons**: People identified in photos
- **Albums**: Album memberships
- **Libraries**: Photo library assignments
- **Titles**: Photo titles
- **Descriptions**: Photo descriptions

## Using the Search Page

1. Navigate to the **🔍 Search** page from the main navigation
2. Select filter values from the available options:
   - Check multiple boxes within each category
   - Selected count is shown next to each category name
3. Optionally enter text to search in titles and descriptions
4. Set a date range if needed
5. Click the **Search Photos** button to execute the search

## Search Logic

- **OR within categories**: If you select multiple values in the same category (e.g., "Paris" and "London" in Places), photos matching ANY of those values will be included.
- **AND between categories**: If you select filters from multiple categories (e.g., Places AND Labels), photos must match ALL selected filter categories.

### Examples

- **Places: Paris, London** → Shows photos from Paris OR London
- **Places: Paris + Labels: Sunset** → Shows photos that are (in Paris) AND (have Sunset label)
- **Keywords: vacation, travel + Persons: John** → Shows photos with (vacation OR travel keywords) AND (John in the photo)

## Database Schema

### search_data Table

The `search_data` table stores searchable metadata with the following structure:

```sql
CREATE TABLE search_data (
    id SERIAL PRIMARY KEY,
    photo_uuid UUID NOT NULL REFERENCES photos(uuid) ON DELETE CASCADE,
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_search_data_photo_key_value UNIQUE (photo_uuid, key, value)
);

CREATE INDEX ix_search_data_photo_uuid ON search_data(photo_uuid);
CREATE INDEX ix_search_data_key ON search_data(key);
CREATE INDEX ix_search_data_value ON search_data(value);
CREATE INDEX ix_search_data_key_value ON search_data(key, value);
```

### Key Types

- `label`: Visual labels
- `keyword`: Keywords and tags
- `person`: People in photos
- `album`: Album memberships
- `place`: Location names (all levels of place hierarchy)
- `library`: Library assignments
- `title`: Photo titles
- `description`: Photo descriptions

## Automatic Population

The `search_data` table is automatically populated when:

- New photos are created via the API
- Existing photos are updated via the API
- Photos are batch imported/updated

## Manual Population

If you need to populate the search_data table for existing photos (e.g., after upgrading), use the CLI command:

```bash
photosafe maintenance populate-search-data
```

This command will:
1. Process all photos in the database
2. Extract searchable metadata
3. Populate the search_data table

**Note**: This operation is safe to run multiple times - it will replace existing search_data entries for each photo.

## API Endpoints

### Get Search Filters

```
GET /api/search/filters
```

Returns available filter values:

```json
{
  "places": ["Paris", "London", "New York", ...],
  "labels": ["sunset", "beach", "mountain", ...],
  "keywords": ["vacation", "family", "work", ...],
  "persons": ["John", "Jane", ...],
  "albums": ["Summer 2023", "Travel", ...],
  "libraries": ["Main Library", ...]
}
```

### Search Photos

```
GET /api/search/
```

Query parameters:
- `places`: Comma-separated place names (OR logic)
- `labels`: Comma-separated labels (OR logic)
- `keywords`: Comma-separated keywords (OR logic)
- `persons`: Comma-separated person names (OR logic)
- `albums`: Comma-separated album names (OR logic)
- `libraries`: Comma-separated library names (OR logic)
- `search_text`: Text to search in titles and descriptions
- `start_date`: ISO date format (YYYY-MM-DD)
- `end_date`: ISO date format (YYYY-MM-DD)
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 50, max: 100)

Example:
```
GET /api/search/?places=Paris,London&labels=sunset&start_date=2023-01-01&page=1&page_size=50
```

Returns paginated photos matching the criteria.

## Performance Considerations

- The `search_data` table has indexes on `photo_uuid`, `key`, `value`, and `(key, value)` for efficient querying
- Unique constraint prevents duplicate entries
- CASCADE delete ensures search_data is cleaned up when photos are deleted
- The table is denormalized for query performance, trading some storage for faster searches

## Maintenance

If search results seem incorrect or incomplete, you can rebuild the search_data table:

```bash
photosafe maintenance populate-search-data
```

This is safe to run at any time and will not affect your photos.
