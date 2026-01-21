# Task System

## Commands

### Place Lookup
Reverse geocodes photos with coordinates but no place data.
```bash
photosafe task lookup-places [--limit N] [--dry-run]
```
Populates `place` JSONB with name, country, admin1/admin2, coordinates.

### Place Summary
Aggregates photo data by location for fast map queries.
```bash
photosafe task update-place-summary [--rebuild]
```
Creates/updates `place_summaries` table with photo counts, date ranges, coordinates.

### List Tasks
```bash
photosafe task list [--status pending|running|completed|failed|all] [--limit N]
```

## API Endpoints

**GET `/api/place-summaries`** - List summaries (params: country, state_province, limit, offset)

**GET `/api/tasks`** - List tasks (params: status, task_type, limit)

## Workflow

```bash
# After importing photos
photosafe task lookup-places      # Fill missing place data
photosafe task update-place-summary   # Update summaries
```

## Models

**Task:** id, name, task_type, status, progress, total, processed, error_message, timestamps, task_metadata

**PlaceSummary:** id, place_name, lat/lng, photo_count, first/last_photo_date, country, state_province, city, place_data
