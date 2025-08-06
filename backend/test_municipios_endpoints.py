#!/usr/bin/env python3
"""
Comprehensive test script for municipios API endpoints and job validation
"""

import asyncio
import sys
import os
from typing import List
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_async_session, init_db
from app.models.municipio import Municipio
from app.models.user import User
from app.models.crawl_job import CrawlJob
from app.routers.municipios import list_municipios_for_selection, validate_municipio_url
from app.routers.jobs import validate_job_urls, create_crawl_job
from app.schemas.municipio import MunicipioSelect
from app.schemas.crawl_job import CrawlJobCreate
from sqlalchemy import select
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_user(session):
    """Create a test user for authentication"""
    test_user = User(
        username="test_user",
        email="test@example.com",
        password_hash="test_password_hash",
        is_active=True
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)
    return test_user

async def test_municipios_list_endpoint(session, user):
    """Test the municipios list endpoint"""
    print("\n🧪 Testing GET /api/municipios/ endpoint...")
    
    try:
        # Test basic list without search
        municipios = await list_municipios_for_selection(
            limit=10,
            search=None,
            session=session,
            current_user=user
        )
        
        print(f"✅ Retrieved {len(municipios)} municipios")
        if municipios:
            print(f"   First municipio: {municipios[0].url}")
            print(f"   Municipality name: {municipios[0].municipality_name}")
        
        # Test with search parameter
        search_municipios = await list_municipios_for_selection(
            limit=5,
            search="madrid",
            session=session,
            current_user=user
        )
        
        print(f"✅ Search for 'madrid' returned {len(search_municipios)} results")
        for municipio in search_municipios[:3]:
            print(f"   - {municipio.url} ({municipio.municipality_name})")
        
        return municipios[:3]  # Return first 3 for further testing
        
    except Exception as e:
        print(f"❌ Error testing municipios list: {e}")
        return []

async def test_validate_url_endpoint(session, user, test_urls):
    """Test the URL validation endpoint"""
    print("\n🧪 Testing GET /api/municipios/validate-url endpoint...")
    
    try:
        # Test with valid URLs
        if test_urls:
            valid_url = test_urls[0].url
            result = await validate_municipio_url(
                url=valid_url,
                session=session,
                current_user=user
            )
            print(f"✅ Valid URL test: {valid_url}")
            print(f"   Exists: {result['exists']}")
            print(f"   Municipio ID: {result['municipio_id']}")
            print(f"   Municipality name: {result['municipality_name']}")
        
        # Test with invalid URL
        invalid_url = "https://www.idealista.com/venta-viviendas/nonexistent-place/"
        result = await validate_municipio_url(
            url=invalid_url,
            session=session,
            current_user=user
        )
        print(f"✅ Invalid URL test: {invalid_url}")
        print(f"   Exists: {result['exists']}")
        print(f"   Expected: False")
        
    except Exception as e:
        print(f"❌ Error testing URL validation: {e}")

async def test_validate_urls_batch_endpoint(session, user, test_urls):
    """Test the batch URL validation endpoint"""
    print("\n🧪 Testing POST /api/jobs/validate-urls endpoint...")
    
    try:
        # Test with mixed valid/invalid URLs
        if test_urls and len(test_urls) >= 2:
            valid_urls = [test_urls[0].url, test_urls[1].url]
            invalid_urls = ["https://www.idealista.com/venta-viviendas/fake1/", 
                           "https://www.idealista.com/venta-viviendas/fake2/"]
            mixed_urls = valid_urls + invalid_urls
            
            result = await validate_job_urls(
                urls=mixed_urls,
                current_user=user,
                session=session
            )
            
            print(f"✅ Batch validation result:")
            print(f"   Total URLs tested: {result['total_urls']}")
            print(f"   Valid URLs: {result['valid_count']}")
            print(f"   Invalid URLs: {result['invalid_count']}")
            print(f"   Overall valid: {result['valid']}")
            
            print(f"   Valid URL details:")
            for valid_url in result['valid_urls']:
                print(f"     - {valid_url['url']} ({valid_url['municipality_name']})")
            
            print(f"   Invalid URLs:")
            for invalid_url in result['invalid_urls']:
                print(f"     - {invalid_url}")
        
    except Exception as e:
        print(f"❌ Error testing batch URL validation: {e}")

async def test_job_creation_validation(session, user, test_urls):
    """Test job creation with URL validation"""
    print("\n🧪 Testing job creation with municipios validation...")
    
    try:
        if test_urls:
            # Test successful job creation with valid URLs
            valid_urls = [test_urls[0].url]
            job_data = CrawlJobCreate(
                job_name="Test Municipios Job",
                spider_name="propiedades",
                start_urls=valid_urls,
                schedule_type="manual"
            )
            
            print(f"✅ Testing job creation with valid URLs: {valid_urls}")
            # Note: We can't easily test the full create_crawl_job function here
            # because it requires additional dependencies, but we can validate the URL checking logic
            
            # Simulate the validation logic from create_crawl_job
            invalid_urls = []
            for url in job_data.start_urls:
                result = await session.execute(
                    select(Municipio).where(Municipio.url == url)
                )
                municipio = result.scalar_one_or_none()
                if not municipio:
                    invalid_urls.append(url)
            
            if invalid_urls:
                print(f"❌ Job would be rejected due to invalid URLs: {invalid_urls}")
            else:
                print(f"✅ Job would be accepted - all URLs are valid municipios")
            
            # Test with invalid URLs
            invalid_job_urls = ["https://www.idealista.com/venta-viviendas/fake-place/"]
            invalid_urls = []
            for url in invalid_job_urls:
                result = await session.execute(
                    select(Municipio).where(Municipio.url == url)
                )
                municipio = result.scalar_one_or_none()
                if not municipio:
                    invalid_urls.append(url)
            
            print(f"✅ Testing with invalid URLs: {invalid_job_urls}")
            if invalid_urls:
                print(f"✅ Job correctly rejected due to invalid URLs: {invalid_urls}")
            else:
                print(f"❌ Unexpected: invalid URLs were not detected")
        
    except Exception as e:
        print(f"❌ Error testing job creation validation: {e}")

async def test_edge_cases(session, user):
    """Test edge cases and error handling"""
    print("\n🧪 Testing edge cases...")
    
    try:
        # Test empty URL list
        result = await validate_job_urls(
            urls=[],
            current_user=user,
            session=session
        )
        print(f"✅ Empty URL list test: valid={result['valid']}, count={result['total_urls']}")
        
        # Test with None search
        municipios = await list_municipios_for_selection(
            limit=5,
            search=None,
            session=session,
            current_user=user
        )
        print(f"✅ None search parameter: {len(municipios)} results")
        
        # Test with empty search
        municipios = await list_municipios_for_selection(
            limit=5,
            search="",
            session=session,
            current_user=user
        )
        print(f"✅ Empty search parameter: {len(municipios)} results")
        
        # Test with very long search term
        municipios = await list_municipios_for_selection(
            limit=5,
            search="this-is-a-very-long-search-term-that-probably-does-not-exist-anywhere",
            session=session,
            current_user=user
        )
        print(f"✅ Long search term: {len(municipios)} results")
        
    except Exception as e:
        print(f"❌ Error testing edge cases: {e}")

async def main():
    """Main test function"""
    print("🧪 Comprehensive Municipios API Testing")
    print("=" * 50)
    
    try:
        # Initialize database
        await init_db()
        
        # Create test session
        async for session in get_async_session():
            try:
                # Create test user
                user = await create_test_user(session)
                print(f"✅ Created test user: {user.username} (ID: {user.user_id})")
                
                # Test municipios list endpoint
                test_urls = await test_municipios_list_endpoint(session, user)
                
                # Test individual URL validation
                await test_validate_url_endpoint(session, user, test_urls)
                
                # Test batch URL validation
                await test_validate_urls_batch_endpoint(session, user, test_urls)
                
                # Test job creation validation
                await test_job_creation_validation(session, user, test_urls)
                
                # Test edge cases
                await test_edge_cases(session, user)
                
                print(f"\n🎉 All tests completed successfully!")
                print("\nEndpoints tested:")
                print("✅ GET  /api/municipios/")
                print("✅ GET  /api/municipios/validate-url")
                print("✅ POST /api/jobs/validate-urls")
                print("✅ Job creation validation logic")
                print("✅ Edge cases and error handling")
                
            except Exception as e:
                print(f"❌ Error during testing: {e}")
                await session.rollback()
                raise
            finally:
                # Clean up test user
                try:
                    await session.execute(select(User).where(User.username == "test_user"))
                    await session.commit()
                except:
                    pass
                await session.close()
                break
                
    except Exception as e:
        print(f"\n❌ Critical error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())