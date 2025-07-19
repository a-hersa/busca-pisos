from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Boolean
from sqlalchemy.sql import func

from app.database import Base

class Property(Base):
    __tablename__ = "propiedades"
    
    p_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(Text)
    url = Column(Text)
    precio = Column(Numeric)
    metros = Column(String(50))
    habitaciones = Column(String(50))
    planta = Column(String(50))
    ascensor = Column(Integer, default=0)
    descripcion = Column(Text)
    poblacion = Column(String(100))
    estatus = Column(String(20), default="activo")
    fecha_crawl = Column(DateTime(timezone=True))
    fecha_updated = Column(DateTime(timezone=True))  # Keep for backward compatibility