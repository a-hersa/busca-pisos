from pydantic import BaseModel
from datetime import date
from typing import Optional

class MunicipioBase(BaseModel):
    url: str
    spider_name: Optional[str] = None

class MunicipioCreate(MunicipioBase):
    pass

class MunicipioUpdate(BaseModel):
    processed: Optional[bool] = None
    spider_name: Optional[str] = None

class MunicipioResponse(MunicipioBase):
    id: int
    fecha_found: Optional[date] = None
    processed: bool = False
    municipality_name: Optional[str] = None

    class Config:
        from_attributes = True

class MunicipioSelect(BaseModel):
    """Simplified schema for dropdown selection"""
    id: int
    url: str
    municipality_name: str
    
    class Config:
        from_attributes = True