# Task System Documentation

## Overview

The PhotoSafe task system provides a simple way to process photos in the background. Tasks can perform operations like looking up place information or generating summary data.

## Features

### 1. Place Lookup Task

The place lookup task uses python-gazetteer to reverse geocode latitude/longitude coordinates and populate the `place` field for photos that have coordinates but no place data.

**Command:**
```bash
photosafe task lookup-places [OPTIONS]
```

**Options:**
- `--limit INTEGER`: Limit the number of photos to process
- `--dry-run`: Show what would be processed without making changes

**Example:**
```bash
# Preview what would be processed
photosafe task lookup-places --dry-run

# Process up to 100 photos
photosafe task lookup-places --limit 100

# Process all photos with missing place data
photosafe task lookup-places
```

**What it does:**
1. Finds all photos with latitude/longitude but no place data
2. Uses GeoNames reverse geocoding to look up location information
3. Populates the `place` JSONB field with:
   - `name`: Location name
   - `country`: Country name
   - `country_code`: Two-letter country code
   - `admin1`: State/Province
   - `admin2`: County/Region
   - `latitude`, `longitude`: Original coordinates

### 2. Place Summary Task

The place summary task aggregates photo data by location to create a summary table. This enables faster map queries without scanning all photos.

**Command:**
```bash
photosafe task update-place-summary [OPTIONS]
```

**Options:**
- `--rebuild`: Rebuild the entire summary table from scratch

**Example:**
```bash
# Update summary table incrementally
photosafe task update-place-summary

# Rebuild from scratch
photosafe task update-place-summary --rebuild
```

**What it does:**
1. Scans all photos with place data
2. Aggregates by place name:
   - Photo count
   - First and last photo dates
   - Geographic coordinates
   - Place hierarchy (country, state, city)
3. Creates or updates records in the `place_summaries` table

### 3. List Tasks

View the status of all tasks.

**Command:**
```bash
photosafe task list [OPTIONS]
```

**Options:**
- `--status [pending|running|completed|failed|all]`: Filter by status (default: all)
- `--limit INTEGER`: Limit number of tasks to show (default: 20)

**Example:**
```bash
# List all tasks
photosafe task list

# List only completed tasks
photosafe task list --status completed

# List last 50 tasks
photosafe task list --limit 50
```

## API Endpoints

### Place Summaries

**GET `/api/place-summaries`**

Get a list of place summaries with photo counts and date ranges.

Query Parameters:
- `level` (default: 2, range: 0-10): Zoom/aggregation level controlling place detail
  - 0-2: Show all places (default)
  - 3-5: Only show places with state/province information
  - 6+: Only show places with city information
- `country` (optional): Filter by country
- `state_province` (optional): Filter by state/province
- `limit` (default: 100, max: 1000): Maximum results
- `offset` (default: 0): Pagination offset

Examples:
```bash
# Get all places (default level 2)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/place-summaries?country=USA&limit=50"

# Get only city-level places (level 6+)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/place-summaries?level=6&limit=50"

# Get only state-level places (level 3-5)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/place-summaries?level=4&country=USA"
```

**GET `/api/place-summaries/{id}`**

Get a specific place summary by ID.

### Tasks

**GET `/api/tasks`**

Get a list of tasks.

Query Parameters:
- `status` (optional): Filter by status (pending, running, completed, failed)
- `task_type` (optional): Filter by task type
- `limit` (default: 20, max: 100): Maximum results

**GET `/api/tasks/{id}`**

Get a specific task by ID.

## Database Models

### Task Model

Tracks background task execution.

Fields:
- `id`: Primary key
- `name`: Task name
- `task_type`: Type of task (lookup_places, update_place_summary)
- `status`: Current status (pending, running, completed, failed)
- `progress`: Progress percentage (0-100)
- `total`: Total items to process
- `processed`: Items processed so far
- `error_message`: Error message if failed
- `created_at`: When task was created
- `started_at`: When task started running
- `completed_at`: When task completed
- `task_metadata`: Additional metadata (JSONB)

### PlaceSummary Model

Aggregated place data for fast map queries.

Fields:
- `id`: Primary key
- `place_name`: Unique place name
- `latitude`, `longitude`: Geographic coordinates
- `photo_count`: Number of photos at this location
- `first_photo_date`: Date of first photo
- `last_photo_date`: Date of last photo
- `country`: Country name
- `state_province`: State/Province
- `city`: City name
- `place_data`: Full place information (JSONB)
- `updated_at`: Last update timestamp

## Usage Patterns

### Initial Setup

1. **Import photos** with location data
2. **Run place lookup** to populate missing place information:
   ```bash
   photosafe task lookup-places
   ```
3. **Build place summary** for fast map loading:
   ```bash
   photosafe task update-place-summary --rebuild
   ```

### Regular Maintenance

After importing new photos:
```bash
# Fill in missing place data
photosafe task lookup-places

# Update summaries
photosafe task update-place-summary
```

### Monitoring

Check task status:
```bash
# List recent tasks
photosafe task list

# Check for failures
photosafe task list --status failed
```

## Performance Considerations

### Place Lookup
- Rate-limited by GeoNames API
- Processes photos in batches of 10
- Can take time for large photo collections
- Use `--limit` for incremental processing

### Place Summary
- Fast aggregation in memory
- Updates in batches of 50
- Use `--rebuild` sparingly (only when needed)

## Error Handling

Tasks track their status and errors:
- **pending**: Not yet started
- **running**: Currently processing
- **completed**: Finished successfully
- **failed**: Encountered an error

Failed tasks include error messages in the `error_message` field.

## Future Enhancements

Potential additions to the task system:
- Task scheduling (cron-like)
- Task dependencies
- Parallel task execution
- Task cancellation
- More task types (thumbnail generation, face detection, etc.)
