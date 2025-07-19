from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional

from app.database import get_async_session
from app.models.property import Property
from app.schemas.property import PropertyResponse
from app.core.deps import get_current_user
from app.services.cache import cache_service

router = APIRouter()

@router.get("/", response_model=List[PropertyResponse])
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    poblacion: Optional[str] = Query(None),
    min_precio: Optional[float] = Query(None),
    max_precio: Optional[float] = Query(None),
    habitaciones: Optional[str] = Query(None),
    ascensor: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("fecha_crawl", regex="^(fecha_crawl|precio|metros|poblacion)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    session: AsyncSession = Depends(get_async_session)
):
    # Generate cache key for this request
    cache_key = cache_service.generate_cache_key(
        "properties_list",
        skip=skip, limit=limit, poblacion=poblacion,
        min_precio=min_precio, max_precio=max_precio,
        habitaciones=habitaciones, ascensor=ascensor,
        search=search, sort_by=sort_by, sort_order=sort_order
    )
    
    # Try to get from cache first
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return cached_result
    
    # Build optimized query with indexes in mind
    query = select(Property)
    
    # Apply filters
    if poblacion:
        query = query.where(Property.poblacion.ilike(f"%{poblacion}%"))
    if min_precio:
        query = query.where(Property.precio >= min_precio)
    if max_precio:
        query = query.where(Property.precio <= max_precio)
    if habitaciones:
        query = query.where(Property.habitaciones.ilike(f"%{habitaciones}%"))
    if ascensor is not None:
        query = query.where(Property.ascensor == (1 if ascensor else 0))
    
    # Global search across multiple fields
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Property.nombre.ilike(search_term) |
            Property.descripcion.ilike(search_term) |
            Property.poblacion.ilike(search_term)
        )
    
    # Apply sorting with proper indexes
    if sort_by == "precio":
        sort_field = Property.precio
    elif sort_by == "metros":
        sort_field = func.cast(Property.metros, func.Numeric)  # Cast string to numeric for proper sorting
    elif sort_by == "poblacion":
        sort_field = Property.poblacion
    else:
        sort_field = Property.fecha_crawl
    
    if sort_order == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    properties = result.scalars().all()
    
    # Cache the result for 5 minutes
    await cache_service.set(cache_key, properties, 300)
    
    return properties

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Property).where(Property.p_id == property_id))
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    return property_obj