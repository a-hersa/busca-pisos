from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import logging

from app.database import get_async_session
from app.models.municipio import Municipio
from app.models.user import User
from app.schemas.municipio import MunicipioResponse, MunicipioSelect, MunicipioCreate, MunicipioUpdate
from app.core.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[MunicipioSelect])
async def list_municipios_for_selection(
    limit: Optional[int] = Query(100, description="Limit number of results"),
    search: Optional[str] = Query(None, description="Search in URL or municipality name"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available municipios for dropdown selection in job creation.
    This endpoint is used by the frontend to populate municipality options.
    """
    try:
        query = select(Municipio).where(Municipio.url.isnot(None))
        
        # Add search filter if provided
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(Municipio.url.ilike(search_term))
        
        # Order by URL for consistent results
        query = query.order_by(Municipio.url).limit(limit)
        
        result = await session.execute(query)
        municipios = result.scalars().all()
        
        # Create response with municipality names extracted from URLs
        response = []
        for municipio in municipios:
            response.append(MunicipioSelect(
                id=municipio.id,
                url=municipio.url,
                municipality_name=municipio.get_municipality_name()
            ))
        
        logger.info(f"Retrieved {len(response)} municipios for user {current_user.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving municipios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving municipios"
        )

@router.get("/all", response_model=List[MunicipioResponse])
async def list_all_municipios(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Limit number of results"),
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    spider_name: Optional[str] = Query(None, description="Filter by spider name"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all municipios with full details (admin use)
    """
    try:
        query = select(Municipio)
        
        # Add filters
        if processed is not None:
            query = query.where(Municipio.processed == processed)
        if spider_name:
            query = query.where(Municipio.spider_name == spider_name)
        
        # Apply pagination and ordering
        query = query.order_by(Municipio.fecha_found.desc(), Municipio.id).offset(skip).limit(limit)
        
        result = await session.execute(query)
        municipios = result.scalars().all()
        
        # Create response with municipality names
        response = []
        for municipio in municipios:
            municipio_data = MunicipioResponse.model_validate(municipio)
            municipio_data.municipality_name = municipio.get_municipality_name()
            response.append(municipio_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving all municipios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving municipios"
        )

@router.get("/stats")
async def get_municipios_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about municipios data
    """
    try:
        # Total count
        total_count = await session.scalar(select(func.count(Municipio.id)))
        
        # Processed count
        processed_count = await session.scalar(
            select(func.count(Municipio.id)).where(Municipio.processed == True)
        )
        
        # Count by spider
        spider_counts = await session.execute(
            select(Municipio.spider_name, func.count(Municipio.id))
            .group_by(Municipio.spider_name)
            .where(Municipio.spider_name.isnot(None))
        )
        spider_stats = dict(spider_counts.fetchall())
        
        return {
            "total_municipios": total_count or 0,
            "processed": processed_count or 0,
            "pending": (total_count or 0) - (processed_count or 0),
            "by_spider": spider_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting municipios stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving municipios statistics"
        )

@router.get("/validate-url")
async def validate_municipio_url(
    url: str = Query(..., description="URL to validate"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Validate if a URL exists in municipios table
    Used by job creation validation
    """
    try:
        result = await session.execute(
            select(Municipio).where(Municipio.url == url)
        )
        municipio = result.scalar_one_or_none()
        
        return {
            "url": url,
            "exists": municipio is not None,
            "municipio_id": municipio.id if municipio else None,
            "municipality_name": municipio.get_municipality_name() if municipio else None
        }
        
    except Exception as e:
        logger.error(f"Error validating URL {url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating URL"
        )

@router.post("/", response_model=MunicipioResponse)
async def create_municipio(
    municipio_data: MunicipioCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new municipio entry (admin use)
    """
    try:
        # Check if URL already exists
        existing = await session.execute(
            select(Municipio).where(Municipio.url == municipio_data.url)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL already exists in municipios"
            )
        
        new_municipio = Municipio(
            url=municipio_data.url,
            spider_name=municipio_data.spider_name
        )
        
        session.add(new_municipio)
        await session.commit()
        await session.refresh(new_municipio)
        
        response = MunicipioResponse.model_validate(new_municipio)
        response.municipality_name = new_municipio.get_municipality_name()
        
        logger.info(f"Created municipio {new_municipio.id} by user {current_user.user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating municipio: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating municipio"
        )

@router.patch("/{municipio_id}", response_model=MunicipioResponse)
async def update_municipio(
    municipio_id: int,
    municipio_update: MunicipioUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update municipio information (admin use)
    """
    try:
        result = await session.execute(
            select(Municipio).where(Municipio.id == municipio_id)
        )
        municipio = result.scalar_one_or_none()
        
        if not municipio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Municipio not found"
            )
        
        # Update fields
        update_data = municipio_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(municipio, field, value)
        
        await session.commit()
        await session.refresh(municipio)
        
        response = MunicipioResponse.model_validate(municipio)
        response.municipality_name = municipio.get_municipality_name()
        
        logger.info(f"Updated municipio {municipio_id} by user {current_user.user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating municipio {municipio_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating municipio"
        )