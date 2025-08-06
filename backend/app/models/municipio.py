from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base

class Municipio(Base):
    __tablename__ = "municipios"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    fecha_found = Column(Date, default=func.current_date())
    spider_name = Column(String(100), index=True)
    processed = Column(Boolean, default=False, index=True)
    
    # Add helper method to extract municipality name from URL if needed
    def get_municipality_name(self) -> str:
        """Extract municipality name from URL for display purposes"""
        try:
            # Extract from idealista URLs like: https://www.idealista.com/venta-viviendas/madrid/madrid/
            parts = self.url.rstrip('/').split('/')
            if len(parts) >= 4:
                return parts[-1].replace('-', ' ').title()
            return "Unknown Municipality"
        except:
            return "Unknown Municipality"