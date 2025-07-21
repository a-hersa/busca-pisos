# FastAPI Routing and Endpoints

## Understanding Routes

Routes are the endpoints that define how your API responds to different HTTP requests. FastAPI uses Python decorators to define routes cleanly and intuitively.

## Basic Route Structure

```python
@app.method("/path")
async def function_name():
    return {"data": "response"}
```

## HTTP Methods

FastAPI supports all standard HTTP methods:

```python
@app.get("/items")          # GET - Retrieve data
@app.post("/items")         # POST - Create new data
@app.put("/items/{id}")     # PUT - Update/replace data
@app.patch("/items/{id}")   # PATCH - Partial update
@app.delete("/items/{id}")  # DELETE - Remove data
```

## Real Examples from Our Project

Let's examine the properties router (`backend/app/routers/properties.py`):

### 1. Basic GET Route
```python
@router.get("/")
async def get_properties(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, le=1000, description="Maximum number of records"),
    session: AsyncSession = Depends(get_async_session)
):
    # Query database
    result = await session.execute(
        select(Property).offset(skip).limit(limit)
    )
    properties = result.scalars().all()
    return properties
```

### 2. Path Parameters
```python
@router.get("/{property_id}")
async def get_property(
    property_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    # Use path parameter to find specific property
    result = await session.execute(
        select(Property).where(Property.p_id == property_id)
    )
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return property_obj
```

### 3. Query Parameters with Validation
```python
@router.get("/search")
async def search_properties(
    poblacion: str = Query(None, description="Filter by location"),
    precio_min: int = Query(None, ge=0, description="Minimum price"),
    precio_max: int = Query(None, ge=0, description="Maximum price"),
    metros_min: int = Query(None, ge=0, description="Minimum square meters"),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(Property)
    
    # Build dynamic query based on parameters
    if poblacion:
        query = query.where(Property.poblacion.ilike(f"%{poblacion}%"))
    if precio_min:
        query = query.where(Property.precio >= precio_min)
    if precio_max:
        query = query.where(Property.precio <= precio_max)
    if metros_min:
        query = query.where(Property.metros >= metros_min)
    
    result = await session.execute(query.limit(100))
    return result.scalars().all()
```

## Router Organization

Our project uses APIRouter to organize endpoints into modules:

```python
# In backend/app/routers/properties.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_properties():
    return {"properties": []}

@router.post("/")
async def create_property():
    return {"message": "Property created"}
```

```python
# In main.py - include the router
from app.routers import properties

app.include_router(
    properties.router, 
    prefix="/api/properties",  # All routes will start with /api/properties
    tags=["properties"]        # Groups endpoints in documentation
)
```

## Request Body Handling

### POST Route with Pydantic Model
From our jobs router (`backend/app/routers/jobs.py`):

```python
@router.post("/", response_model=CrawlJobResponse)
async def create_crawl_job(
    job_data: CrawlJobCreate,  # Pydantic model validates request body
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Create new job from validated data
    job = CrawlJob(
        job_name=job_data.job_name,
        spider_name=job_data.spider_name,
        target_urls=job_data.target_urls,
        schedule_type=job_data.schedule_type,
        created_by=current_user.user_id,
        status="pending"
    )
    
    session.add(job)
    await session.commit()
    await session.refresh(job)
    
    return job
```

## Response Models

FastAPI can automatically serialize responses using Pydantic models:

```python
from app.schemas.property import PropertyResponse

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: int):
    # FastAPI will automatically convert the result to PropertyResponse format
    return property_obj
```

## Error Handling

```python
from fastapi import HTTPException

@router.get("/{property_id}")
async def get_property(property_id: int):
    property_obj = await find_property(property_id)
    
    if not property_obj:
        raise HTTPException(
            status_code=404, 
            detail="Property not found"
        )
    
    return property_obj
```

## Advanced Routing Features

### 1. Multiple Path Parameters
```python
@router.get("/users/{user_id}/properties/{property_id}")
async def get_user_property(user_id: int, property_id: int):
    return {"user_id": user_id, "property_id": property_id}
```

### 2. Optional Path Parameters
```python
@router.get("/properties/{property_id}/images/{image_id}")
async def get_property_image(
    property_id: int, 
    image_id: int = None
):
    if image_id:
        return {"property": property_id, "image": image_id}
    return {"property": property_id, "all_images": True}
```

### 3. Route Dependencies
```python
# Apply authentication to all routes in this router
router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/protected-endpoint")
async def protected_route():
    # This route automatically requires authentication
    return {"message": "Only authenticated users see this"}
```

## Status Codes

```python
from fastapi import status

@router.post("/properties", status_code=status.HTTP_201_CREATED)
async def create_property():
    return {"message": "Property created"}

@router.delete("/properties/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property():
    # Returns empty response with 204 status
    pass
```

## Tags and Documentation

```python
@router.get(
    "/properties/analytics",
    tags=["analytics"],
    summary="Get property analytics",
    description="Returns statistical analysis of properties including price trends",
    response_description="Analytics data with trends and statistics"
)
async def get_property_analytics():
    return {"analytics": "data"}
```

## Practice Exercises

1. **Create a new router** for managing property favorites:
   - POST `/favorites` - Add property to favorites
   - GET `/favorites` - List user's favorite properties
   - DELETE `/favorites/{property_id}` - Remove from favorites

2. **Add query parameters** to the properties list endpoint:
   - `sort_by`: precio, metros, fecha_updated
   - `order`: asc, desc
   - `status`: activo, inactivo

3. **Implement search functionality** with multiple filters that can be combined

## Next Steps

In the next guide, we'll explore:
- Pydantic models for request/response validation
- Dependency injection system
- Database integration patterns