from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_async_session
from app.models.user import User
from app.models.property import Property
from app.models.crawl_job import CrawlJob, JobExecution
from app.core.deps import get_current_user
from typing import Optional, List
import csv
import json
import io
from datetime import datetime
import xlsxwriter

router = APIRouter()

@router.get("/properties/csv")
async def export_properties_csv(
    poblacion: Optional[str] = Query(None),
    min_precio: Optional[float] = Query(None),
    max_precio: Optional[float] = Query(None),
    limit: int = Query(1000, le=10000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Export properties to CSV format
    """
    # Build query
    query = select(Property)
    
    # Apply filters
    if poblacion:
        query = query.where(Property.poblacion.ilike(f"%{poblacion}%"))
    if min_precio:
        query = query.where(Property.precio >= min_precio)
    if max_precio:
        query = query.where(Property.precio <= max_precio)
    
    query = query.limit(limit)
    
    # Execute query
    result = await session.execute(query)
    properties = result.scalars().all()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        'ID', 'Nombre', 'URL', 'Precio', 'Metros', 'Habitaciones', 
        'Planta', 'Ascensor', 'Descripción', 'Población', 'Estado',
        'Fecha Crawl', 'Fecha Actualización'
    ]
    writer.writerow(headers)
    
    # Write data
    for prop in properties:
        writer.writerow([
            prop.p_id,
            prop.nombre or '',
            prop.url or '',
            prop.precio or '',
            prop.metros or '',
            prop.habitaciones or '',
            prop.planta or '',
            prop.ascensor,
            prop.descripcion or '',
            prop.poblacion or '',
            prop.estatus,
            prop.fecha_crawl.isoformat() if prop.fecha_crawl else '',
            prop.fecha_updated.isoformat() if prop.fecha_updated else ''
        ])
    
    output.seek(0)
    
    # Create response
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=propiedades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )
    
    return response

@router.get("/properties/excel")
async def export_properties_excel(
    poblacion: Optional[str] = Query(None),
    min_precio: Optional[float] = Query(None),
    max_precio: Optional[float] = Query(None),
    limit: int = Query(1000, le=10000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Export properties to Excel format
    """
    # Build query
    query = select(Property)
    
    # Apply filters
    if poblacion:
        query = query.where(Property.poblacion.ilike(f"%{poblacion}%"))
    if min_precio:
        query = query.where(Property.precio >= min_precio)
    if max_precio:
        query = query.where(Property.precio <= max_precio)
    
    query = query.limit(limit)
    
    # Execute query
    result = await session.execute(query)
    properties = result.scalars().all()
    
    # Create Excel content in memory
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Propiedades')
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    currency_format = workbook.add_format({'num_format': '€#,##0'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm'})
    
    # Write headers
    headers = [
        'ID', 'Nombre', 'URL', 'Precio', 'Metros', 'Habitaciones', 
        'Planta', 'Ascensor', 'Descripción', 'Población', 'Estado',
        'Fecha Crawl', 'Fecha Actualización'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Write data
    for row, prop in enumerate(properties, 1):
        worksheet.write(row, 0, prop.p_id)
        worksheet.write(row, 1, prop.nombre or '')
        worksheet.write(row, 2, prop.url or '')
        worksheet.write(row, 3, prop.precio or '', currency_format if prop.precio else None)
        worksheet.write(row, 4, prop.metros or '')
        worksheet.write(row, 5, prop.habitaciones or '')
        worksheet.write(row, 6, prop.planta or '')
        worksheet.write(row, 7, 'Sí' if prop.ascensor else 'No')
        worksheet.write(row, 8, prop.descripcion or '')
        worksheet.write(row, 9, prop.poblacion or '')
        worksheet.write(row, 10, prop.estatus)
        worksheet.write(row, 11, prop.fecha_crawl, date_format if prop.fecha_crawl else None)
        worksheet.write(row, 12, prop.fecha_updated, date_format if prop.fecha_updated else None)
    
    # Auto-adjust column widths
    worksheet.set_column('A:A', 8)   # ID
    worksheet.set_column('B:B', 30)  # Nombre
    worksheet.set_column('C:C', 40)  # URL
    worksheet.set_column('D:D', 12)  # Precio
    worksheet.set_column('E:E', 10)  # Metros
    worksheet.set_column('F:F', 12)  # Habitaciones
    worksheet.set_column('G:G', 10)  # Planta
    worksheet.set_column('H:H', 10)  # Ascensor
    worksheet.set_column('I:I', 40)  # Descripción
    worksheet.set_column('J:J', 15)  # Población
    worksheet.set_column('K:K', 10)  # Estado
    worksheet.set_column('L:M', 18)  # Fechas
    
    workbook.close()
    output.seek(0)
    
    # Create response
    response = StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=propiedades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )
    
    return response

@router.get("/jobs/csv")
async def export_jobs_csv(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Export user's crawl jobs to CSV format
    """
    # Get user's jobs
    result = await session.execute(
        select(CrawlJob).where(CrawlJob.created_by == current_user.user_id)
    )
    jobs = result.scalars().all()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        'ID', 'Nombre', 'Spider', 'URLs', 'Estado', 'Tipo Programación',
        'Expresión Cron', 'Próxima Ejecución', 'Creado', 'Actualizado'
    ]
    writer.writerow(headers)
    
    # Write data
    for job in jobs:
        writer.writerow([
            job.job_id,
            job.job_name,
            job.spider_name,
            '; '.join(job.start_urls),
            job.status,
            job.schedule_type,
            job.cron_expression or '',
            job.next_run.isoformat() if job.next_run else '',
            job.created_at.isoformat(),
            job.updated_at.isoformat()
        ])
    
    output.seek(0)
    
    # Create response
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )
    
    return response

@router.get("/analytics/json")
async def export_analytics_json(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Export analytics data in JSON format
    """
    # Properties by location
    location_query = text("""
        SELECT poblacion, COUNT(*) as count, AVG(precio) as avg_price
        FROM propiedades 
        WHERE poblacion IS NOT NULL AND poblacion != ''
        GROUP BY poblacion
        ORDER BY count DESC
        LIMIT 20
    """)
    location_result = await session.execute(location_query)
    location_data = [
        {
            "poblacion": row.poblacion,
            "count": row.count,
            "avg_price": float(row.avg_price) if row.avg_price else 0
        }
        for row in location_result
    ]
    
    # Price distribution
    price_query = text("""
        SELECT 
            CASE 
                WHEN precio < 50000 THEN 'Menos de 50k'
                WHEN precio < 100000 THEN '50k - 100k'
                WHEN precio < 200000 THEN '100k - 200k'
                WHEN precio < 500000 THEN '200k - 500k'
                ELSE 'Más de 500k'
            END as price_range,
            COUNT(*) as count
        FROM propiedades 
        WHERE precio IS NOT NULL
        GROUP BY price_range
        ORDER BY 
            CASE 
                WHEN precio < 50000 THEN 1
                WHEN precio < 100000 THEN 2
                WHEN precio < 200000 THEN 3
                WHEN precio < 500000 THEN 4
                ELSE 5
            END
    """)
    price_result = await session.execute(price_query)
    price_data = [
        {
            "price_range": row.price_range,
            "count": row.count
        }
        for row in price_result
    ]
    
    # Job executions stats
    if current_user.role == 'admin':
        job_stats_query = text("""
            SELECT 
                DATE(started_at) as date,
                status,
                COUNT(*) as count,
                SUM(items_scraped) as total_items
            FROM job_executions
            WHERE started_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(started_at), status
            ORDER BY date DESC
        """)
        job_stats_result = await session.execute(job_stats_query)
        job_stats_data = [
            {
                "date": row.date.isoformat() if row.date else None,
                "status": row.status,
                "count": row.count,
                "total_items": row.total_items or 0
            }
            for row in job_stats_result
        ]
    else:
        job_stats_data = []
    
    # Compile analytics data
    analytics_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "user_id": current_user.user_id,
        "location_stats": location_data,
        "price_distribution": price_data,
        "job_execution_stats": job_stats_data
    }
    
    # Create JSON response
    json_content = json.dumps(analytics_data, indent=2, ensure_ascii=False)
    
    response = Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )
    
    return response