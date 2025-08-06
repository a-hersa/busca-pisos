# Municipios API Documentation

This document describes the new municipios API endpoints that restrict crawl job creation to validated municipality URLs.

## Overview

The municipios system ensures that crawl jobs can only be created with starting URLs that exist in the `municipios` table. This table is populated by the `municipios` spider and contains validated municipality URLs from idealista.com.

## Database Schema

### Municipios Table
```sql
CREATE TABLE municipios (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    fecha_found DATE DEFAULT CURRENT_DATE,
    spider_name VARCHAR(100),
    processed BOOLEAN DEFAULT FALSE
);
```

## API Endpoints

### 1. Get Municipios for Selection
**GET** `/api/municipios/`

Returns a list of municipios suitable for dropdown selection in job creation forms.

**Query Parameters:**
- `limit` (optional): Maximum number of results (default: 100)
- `search` (optional): Search term to filter URLs

**Response:**
```json
[
    {
        "id": 1,
        "url": "https://www.idealista.com/venta-viviendas/madrid/madrid/",
        "municipality_name": "Madrid"
    },
    {
        "id": 2,
        "url": "https://www.idealista.com/venta-viviendas/barcelona/barcelona/",
        "municipality_name": "Barcelona"
    }
]
```

### 2. Get All Municipios (Admin)
**GET** `/api/municipios/all`

Returns detailed information about all municipios (admin use).

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of results (default: 100)
- `processed` (optional): Filter by processed status (true/false)
- `spider_name` (optional): Filter by spider name

**Response:**
```json
[
    {
        "id": 1,
        "url": "https://www.idealista.com/venta-viviendas/madrid/madrid/",
        "fecha_found": "2024-08-06",
        "spider_name": "municipios",
        "processed": false,
        "municipality_name": "Madrid"
    }
]
```

### 3. Get Municipios Statistics
**GET** `/api/municipios/stats`

Returns statistics about the municipios data.

**Response:**
```json
{
    "total_municipios": 150,
    "processed": 25,
    "pending": 125,
    "by_spider": {
        "municipios": 150
    }
}
```

### 4. Validate Single URL
**GET** `/api/municipios/validate-url?url=<url>`

Validates if a single URL exists in the municipios table.

**Query Parameters:**
- `url` (required): URL to validate

**Response:**
```json
{
    "url": "https://www.idealista.com/venta-viviendas/madrid/madrid/",
    "exists": true,
    "municipio_id": 1,
    "municipality_name": "Madrid"
}
```

### 5. Validate Multiple URLs for Job Creation
**POST** `/api/jobs/validate-urls`

Validates multiple URLs for job creation (part of jobs API).

**Request Body:**
```json
["https://www.idealista.com/venta-viviendas/madrid/madrid/", "https://www.idealista.com/venta-viviendas/barcelona/barcelona/"]
```

**Response:**
```json
{
    "valid": true,
    "valid_urls": [
        {
            "url": "https://www.idealista.com/venta-viviendas/madrid/madrid/",
            "municipio_id": 1,
            "municipality_name": "Madrid"
        }
    ],
    "invalid_urls": [],
    "total_urls": 1,
    "valid_count": 1,
    "invalid_count": 0
}
```

### 6. Create Municipio (Admin)
**POST** `/api/municipios/`

Creates a new municipio entry.

**Request Body:**
```json
{
    "url": "https://www.idealista.com/venta-viviendas/valencia/valencia/",
    "spider_name": "manual"
}
```

### 7. Update Municipio (Admin)
**PATCH** `/api/municipios/{municipio_id}`

Updates a municipio entry.

**Request Body:**
```json
{
    "processed": true
}
```

## Job Creation Validation

### Updated Job Creation
When creating or updating crawl jobs, all `start_urls` are now validated against the municipios table.

**Example Error Response (Invalid URLs):**
```json
{
    "message": "Some URLs are not valid municipios",
    "invalid_urls": [
        "https://example.com/invalid-url"
    ],
    "hint": "Only URLs from the municipios table are allowed as starting URLs"
}
```

## Frontend Integration

### Dropdown Population
Use the `/api/municipios/` endpoint to populate dropdown options:

```javascript
// Fetch municipios for dropdown
const response = await fetch('/api/municipios/?limit=200');
const municipios = await response.json();

// Populate select options
municipios.forEach(municipio => {
    const option = document.createElement('option');
    option.value = municipio.url;
    option.textContent = municipio.municipality_name;
    municipioSelect.appendChild(option);
});
```

### URL Validation
Validate URLs before job creation:

```javascript
// Validate URLs before submitting job
const validateUrls = async (urls) => {
    const response = await fetch('/api/jobs/validate-urls', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(urls)
    });
    return response.json();
};

const validation = await validateUrls([selectedUrl]);
if (!validation.valid) {
    alert(`Invalid URLs: ${validation.invalid_urls.join(', ')}`);
    return;
}
```

## Migration Guide

### For Existing Installations

1. **Run Migration Script:**
   ```sql
   -- Run backend/migrations/001_add_municipios_constraints.sql
   ```

2. **Populate Municipios Table:**
   ```bash
   # Run municipios spider to populate the table
   cd backend
   scrapy crawl municipios
   ```

3. **Update Frontend:**
   - Replace manual URL input with municipios dropdown
   - Add URL validation before job submission
   - Handle validation error responses

### Testing

Run the test script to verify functionality:

```bash
cd backend
python utils/test_municipios_api.py
```

## Security Considerations

- All endpoints require authentication
- Only authenticated users can access municipios data
- Admin endpoints may be restricted further based on user roles
- URL validation prevents unauthorized scraping targets

## Performance Notes

- The municipios table is indexed on `url`, `spider_name`, and `processed` columns
- Consider pagination for large datasets
- Use search parameters to filter results efficiently
- Cache municipios data on the frontend to reduce API calls