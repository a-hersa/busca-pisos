from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from app.database import get_async_session
from app.models.user import User
from app.models.property import Property
from app.models.crawl_job import CrawlJob, JobExecution
from app.core.deps import get_current_user
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard statistics
    """
    # Properties by location
    location_query = text("""
        SELECT poblacion, COUNT(*) as count, AVG(precio) as avg_price
        FROM propiedades 
        WHERE poblacion IS NOT NULL AND poblacion != ''
        GROUP BY poblacion
        ORDER BY count DESC
        LIMIT 10
    """)
    location_result = await session.execute(location_query)
    location_stats = [
        {
            "name": row.poblacion,
            "count": row.count,
            "avg_price": round(float(row.avg_price)) if row.avg_price else 0
        }
        for row in location_result
    ]
    
    # Price distribution
    price_query = text("""
        WITH price_ranges AS (
            SELECT 
                CASE 
                    WHEN precio < 50000 THEN '< 50k'
                    WHEN precio < 100000 THEN '50k-100k'
                    WHEN precio < 200000 THEN '100k-200k'
                    WHEN precio < 500000 THEN '200k-500k'
                    ELSE '> 500k'
                END as price_range,
                CASE 
                    WHEN precio < 50000 THEN 1
                    WHEN precio < 100000 THEN 2
                    WHEN precio < 200000 THEN 3
                    WHEN precio < 500000 THEN 4
                    ELSE 5
                END as sort_order
            FROM propiedades 
            WHERE precio IS NOT NULL
        )
        SELECT price_range, COUNT(*) as count
        FROM price_ranges
        GROUP BY price_range, sort_order
        ORDER BY sort_order
    """)
    price_result = await session.execute(price_query)
    price_distribution = [
        {
            "range": row.price_range,
            "count": row.count
        }
        for row in price_result
    ]
    
    # Property trends (last 30 days)
    trends_query = text("""
        SELECT 
            DATE(fecha_crawl) as date,
            COUNT(*) as properties_found,
            AVG(precio) as avg_price
        FROM propiedades 
        WHERE fecha_crawl >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(fecha_crawl)
        ORDER BY date DESC
        LIMIT 30
    """)
    trends_result = await session.execute(trends_query)
    property_trends = [
        {
            "date": row.date.isoformat() if row.date else None,
            "properties_found": row.properties_found,
            "avg_price": round(float(row.avg_price)) if row.avg_price else 0
        }
        for row in trends_result
    ]
    
    # Job statistics
    if current_user.role == 'admin':
        # Admin sees all jobs
        job_stats_query = text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM crawl_jobs
            GROUP BY status
        """)
        
        execution_stats_query = text("""
            SELECT 
                DATE(started_at) as date,
                COUNT(*) as executions,
                SUM(items_scraped) as total_items,
                AVG(
                    CASE 
                        WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (completed_at - started_at))/60 
                    END
                ) as avg_duration_minutes
            FROM job_executions
            WHERE started_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(started_at)
            ORDER BY date DESC
            LIMIT 30
        """)
    else:
        # Regular users see only their jobs
        job_stats_query = text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM crawl_jobs
            WHERE created_by = :user_id
            GROUP BY status
        """)
        
        execution_stats_query = text("""
            SELECT 
                DATE(je.started_at) as date,
                COUNT(*) as executions,
                SUM(je.items_scraped) as total_items,
                AVG(
                    CASE 
                        WHEN je.completed_at IS NOT NULL AND je.started_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (je.completed_at - je.started_at))/60 
                    END
                ) as avg_duration_minutes
            FROM job_executions je
            JOIN crawl_jobs cj ON je.job_id = cj.job_id
            WHERE je.started_at >= NOW() - INTERVAL '30 days'
            AND cj.created_by = :user_id
            GROUP BY DATE(je.started_at)
            ORDER BY date DESC
            LIMIT 30
        """)
    
    job_stats_result = await session.execute(
        job_stats_query, 
        {"user_id": current_user.user_id} if current_user.role != 'admin' else {}
    )
    job_statistics = [
        {
            "status": row.status,
            "count": row.count
        }
        for row in job_stats_result
    ]
    
    execution_stats_result = await session.execute(
        execution_stats_query,
        {"user_id": current_user.user_id} if current_user.role != 'admin' else {}
    )
    execution_trends = [
        {
            "date": row.date.isoformat() if row.date else None,
            "executions": row.executions,
            "total_items": row.total_items or 0,
            "avg_duration_minutes": round(float(row.avg_duration_minutes), 2) if row.avg_duration_minutes else 0
        }
        for row in execution_stats_result
    ]
    
    # Summary statistics
    total_properties_result = await session.execute(
        text("SELECT COUNT(*) as count FROM propiedades")
    )
    total_properties = total_properties_result.scalar()
    
    active_properties_result = await session.execute(
        text("SELECT COUNT(*) as count FROM propiedades WHERE estatus = 'activo'")
    )
    active_properties = active_properties_result.scalar()
    
    avg_price_result = await session.execute(
        text("SELECT AVG(precio) as avg_price FROM propiedades WHERE precio IS NOT NULL")
    )
    avg_price = avg_price_result.scalar()
    
    return {
        "summary": {
            "total_properties": total_properties,
            "active_properties": active_properties,
            "avg_price": round(float(avg_price)) if avg_price else 0,
            "total_locations": len(location_stats)
        },
        "location_stats": location_stats,
        "price_distribution": price_distribution,
        "property_trends": property_trends,
        "job_statistics": job_statistics,
        "execution_trends": execution_trends,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/properties/by-location")
async def get_properties_by_location(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Get detailed property statistics by location
    """
    query = text("""
        SELECT 
            poblacion,
            COUNT(*) as total_count,
            COUNT(CASE WHEN estatus = 'activo' THEN 1 END) as active_count,
            AVG(precio) as avg_price,
            MIN(precio) as min_price,
            MAX(precio) as max_price,
            AVG(CASE WHEN metros ~ '^[0-9]+$' THEN metros::integer END) as avg_meters
        FROM propiedades 
        WHERE poblacion IS NOT NULL AND poblacion != ''
        GROUP BY poblacion
        HAVING COUNT(*) >= 5
        ORDER BY total_count DESC
        LIMIT 20
    """)
    
    result = await session.execute(query)
    
    return [
        {
            "location": row.poblacion,
            "total_properties": row.total_count,
            "active_properties": row.active_count,
            "avg_price": round(float(row.avg_price)) if row.avg_price else 0,
            "min_price": round(float(row.min_price)) if row.min_price else 0,
            "max_price": round(float(row.max_price)) if row.max_price else 0,
            "avg_meters": round(float(row.avg_meters)) if row.avg_meters else 0,
            "price_per_m2": round(float(row.avg_price) / float(row.avg_meters)) if row.avg_price and row.avg_meters else 0
        }
        for row in result
    ]

@router.get("/job-performance")
async def get_job_performance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get job execution performance metrics
    """
    # Base query conditions
    if current_user.role == 'admin':
        job_condition = ""
        params = {}
    else:
        job_condition = "AND cj.created_by = :user_id"
        params = {"user_id": current_user.user_id}
    
    # Success rate by spider
    spider_stats_query = text(f"""
        SELECT 
            cj.spider_name,
            COUNT(*) as total_executions,
            COUNT(CASE WHEN je.status = 'completed' THEN 1 END) as successful_executions,
            SUM(je.items_scraped) as total_items,
            AVG(je.items_scraped) as avg_items_per_run,
            AVG(
                CASE 
                    WHEN je.completed_at IS NOT NULL AND je.started_at IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (je.completed_at - je.started_at))/60 
                END
            ) as avg_duration_minutes
        FROM job_executions je
        JOIN crawl_jobs cj ON je.job_id = cj.job_id
        WHERE je.started_at >= NOW() - INTERVAL '30 days'
        {job_condition}
        GROUP BY cj.spider_name
        ORDER BY total_executions DESC
    """)
    
    spider_result = await session.execute(spider_stats_query, params)
    spider_performance = [
        {
            "spider_name": row.spider_name,
            "total_executions": row.total_executions,
            "successful_executions": row.successful_executions,
            "success_rate": round((row.successful_executions / row.total_executions) * 100, 2) if row.total_executions > 0 else 0,
            "total_items": row.total_items or 0,
            "avg_items_per_run": round(float(row.avg_items_per_run), 2) if row.avg_items_per_run else 0,
            "avg_duration_minutes": round(float(row.avg_duration_minutes), 2) if row.avg_duration_minutes else 0
        }
        for row in spider_result
    ]
    
    # Execution trends over time
    trends_query = text(f"""
        SELECT 
            DATE(je.started_at) as date,
            COUNT(*) as total_executions,
            COUNT(CASE WHEN je.status = 'completed' THEN 1 END) as successful_executions,
            COUNT(CASE WHEN je.status = 'failed' THEN 1 END) as failed_executions,
            SUM(je.items_scraped) as total_items
        FROM job_executions je
        JOIN crawl_jobs cj ON je.job_id = cj.job_id
        WHERE je.started_at >= NOW() - INTERVAL '30 days'
        {job_condition}
        GROUP BY DATE(je.started_at)
        ORDER BY date DESC
        LIMIT 30
    """)
    
    trends_result = await session.execute(trends_query, params)
    execution_trends = [
        {
            "date": row.date.isoformat() if row.date else None,
            "total_executions": row.total_executions,
            "successful_executions": row.successful_executions,
            "failed_executions": row.failed_executions,
            "success_rate": round((row.successful_executions / row.total_executions) * 100, 2) if row.total_executions > 0 else 0,
            "total_items": row.total_items or 0
        }
        for row in trends_result
    ]
    
    return {
        "spider_performance": spider_performance,
        "execution_trends": execution_trends,
        "generated_at": datetime.utcnow().isoformat()
    }