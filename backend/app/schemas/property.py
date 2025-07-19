from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class PropertyResponse(BaseModel):
    p_id: int
    nombre: Optional[str]
    url: Optional[str]
    precio: Optional[Decimal]
    metros: Optional[str]
    habitaciones: Optional[str]
    planta: Optional[str]
    ascensor: int
    descripcion: Optional[str]
    poblacion: Optional[str]
    estatus: str
    fecha_crawl: Optional[datetime]
    fecha_updated: Optional[datetime]

    class Config:
        from_attributes = True