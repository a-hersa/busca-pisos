#!/usr/bin/env python3
"""
Test script for municipios API endpoints
Run this script to test the municipios functionality
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_async_session, init_db
from app.models.municipio import Municipio
from sqlalchemy import select

async def test_municipios():
    """Test municipios functionality"""
    # Initialize database
    await init_db()
    
    # Create test session
    async for session in get_async_session():
        try:
            # Test 1: Check if municipios table has data
            result = await session.execute(select(Municipio))
            municipios = result.scalars().all()
            print(f"Found {len(municipios)} municipios in database")
            
            # Test 2: Show first 5 municipios
            if municipios:
                print("\nFirst 5 municipios:")
                for i, municipio in enumerate(municipios[:5]):
                    print(f"{i+1}. ID: {municipio.id}")
                    print(f"   URL: {municipio.url}")
                    print(f"   Municipality Name: {municipio.get_municipality_name()}")
                    print(f"   Spider: {municipio.spider_name}")
                    print(f"   Processed: {municipio.processed}")
                    print(f"   Date Found: {municipio.fecha_found}")
                    print()
            
            # Test 3: Check for specific URL
            test_url = "https://www.idealista.com/venta-viviendas/madrid/madrid/"
            result = await session.execute(
                select(Municipio).where(Municipio.url == test_url)
            )
            test_municipio = result.scalar_one_or_none()
            
            if test_municipio:
                print(f"✅ Test URL found in database: {test_url}")
                print(f"   Municipality: {test_municipio.get_municipality_name()}")
            else:
                print(f"❌ Test URL not found in database: {test_url}")
                print("   This URL would be rejected for job creation")
            
            # Test 4: Add a test municipio if none exist
            if not municipios:
                print("\n🔧 Adding test municipio...")
                test_municipio = Municipio(
                    url="https://www.idealista.com/venta-viviendas/madrid/madrid/",
                    spider_name="test",
                    processed=False
                )
                session.add(test_municipio)
                await session.commit()
                await session.refresh(test_municipio)
                print(f"✅ Test municipio added with ID: {test_municipio.id}")
            
        except Exception as e:
            print(f"Error during testing: {e}")
            await session.rollback()
            
        finally:
            await session.close()
            break

def main():
    """Main test function"""
    print("🧪 Testing Municipios API functionality...")
    print("=" * 50)
    
    try:
        asyncio.run(test_municipios())
        print("\n✅ Municipios test completed successfully!")
        print("\nAPI Endpoints available:")
        print("- GET  /api/municipios/           # Get municipios for selection")
        print("- GET  /api/municipios/all        # Get all municipios (admin)")
        print("- GET  /api/municipios/stats      # Get municipios statistics")
        print("- POST /api/jobs/validate-urls    # Validate URLs for job creation")
        print("- GET  /api/municipios/validate-url?url=<url>  # Validate single URL")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()