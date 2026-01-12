# Frontend Shared Utilities and Components

This document describes the shared utilities and components available in the PhotoSafe frontend to reduce code duplication.

## Formatting Utilities (`src/utils/format.ts`)

### `formatDate(dateString, options?)`
Formats an ISO date string for display.

**Parameters:**
- `dateString` (string, optional): ISO date string (UTC if no timezone)
- `options` (object, optional):
  - `exifOffset` (string): EXIF timezone offset (e.g., "+05:00")
  - `style` ("full" | "short"): Format style (default: "full" with time)

**Returns:** Formatted date string or "Unknown"

**Examples:**
```typescript
formatDate("2024-01-15T14:30:00Z") 
// "Jan 15, 2024, 02:30 PM"

formatDate("2024-01-15T14:30:00Z", { style: "short" })
// "Jan 15, 2024"

formatDate("2024-01-15T14:30:00", { exifOffset: "+05:00" })
// Applies timezone offset from EXIF data
```

### `formatFileSize(bytes)`
Formats a file size in bytes to a human-readable string.

**Parameters:**
- `bytes` (number, optional): File size in bytes

**Returns:** Formatted size string (e.g., "1.5 MB") or "Unknown"

**Examples:**
```typescript
formatFileSize(1572864)  // "1.5 MB"
formatFileSize(1536)     // "1.5 KB"
formatFileSize(500)      // "500 B"
```

### `formatDateRange(startDate, endDate)`
Formats a date range, showing only years if the range spans multiple years.

**Parameters:**
- `startDate` (string): ISO start date
- `endDate` (string): ISO end date

**Returns:** Formatted range string

**Examples:**
```typescript
formatDateRange("2024-01-01", "2024-12-31")
// "Photos from 2024"

formatDateRange("2020-01-01", "2024-12-31")
// "2020 - 2024"
```

## Error Handling Utilities (`src/utils/errorHandling.ts`)

### `formatApiError(error)`
Formats an API error for display to users.

**Parameters:**
- `error` (unknown): The error object from an API call

**Returns:** User-friendly error message string

**Features:**
- Handles Axios-like errors
- Provides specific messages for HTTP status codes (401, 403, 404)
- Detects network errors
- Extracts detailed error messages from API responses

**Example:**
```typescript
try {
  await login(username, password);
} catch (err) {
  const message = formatApiError(err);
  // Display user-friendly message
}
```

### `logError(context, error)`
Logs an error to the console with context.

**Parameters:**
- `context` (string): Description of where/what was happening
- `error` (unknown): The error object

**Example:**
```typescript
try {
  await loadPhoto(uuid);
} catch (err) {
  logError("Load photo", err);
}
```

## Image URL Utilities (`src/utils/imageUrl.ts`)

### `buildS3Url(s3Path)`
Builds a full S3 URL from a relative path.

### `getDetailImageUrl(photo)`
Gets the highest quality image URL available for a photo.

### `getShareUrl(photo)`
Gets the best share URL for a photo (prioritizes medium/edited versions).

## Place Formatting (`src/utils/formatPlace.ts`)

### `formatPlace(place)`
Formats a place object for display, showing top-level fields.

## Shared Components

### LoadingSpinner (`src/components/LoadingSpinner.vue`)

A reusable loading spinner component with optional message.

**Props:**
- `message` (string, optional): Loading message to display
- `size` ("small" | "medium" | "large", default: "medium"): Spinner size
- `containerClass` (string, optional): Additional CSS class for container

**Usage:**
```vue
<template>
  <LoadingSpinner message="Loading photos..." />
  <LoadingSpinner size="small" message="Loading more..." />
</template>

<script setup>
import LoadingSpinner from "@/components/LoadingSpinner.vue";
</script>
```

## Shared Styles (`src/styles/shared.css`)

CSS variables and common styles for consistent theming.

**CSS Variables Available:**
```css
/* Colors */
--color-background: #121212
--color-surface: #1e1e1e
--color-surface-elevated: #2a2a2a
--color-border: #3a3a3a
--color-primary: #667eea
--color-text-primary: #e0e0e0
--color-text-secondary: #b0b0b0
--color-error: #ff4444
--color-success: #44aa44

/* Spacing */
--spacing-sm: 0.5rem
--spacing-md: 1rem
--spacing-lg: 1.5rem
--spacing-xl: 2rem

/* Border radius */
--radius-md: 8px
--radius-lg: 12px

/* Shadows */
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3)
```

**Common CSS Classes:**
- `.spinner` - Standard loading spinner
- `.loading-state` - Container for loading state
- `.empty-state` - Container for empty state
- `.card` - Card container style
- `.form-group` - Form field group
- `.error-message` / `.success-message` - Message boxes
- `.button-primary` - Primary button style
- `.sidebar` - Sidebar container

## Best Practices

1. **Always use shared utilities** instead of duplicating code
2. **Import only what you need** to keep bundle size small
3. **Use LoadingSpinner component** instead of custom spinner HTML/CSS
4. **Use error handling utilities** for consistent error messages
5. **Use CSS variables** for colors and spacing to maintain consistency
6. **Add tests** for any new shared utilities

## Testing

All utility functions have comprehensive test coverage. See:
- `src/utils/format.test.ts`
- `src/utils/imageUrl.test.ts`

Run tests with: `npm run test:run`
