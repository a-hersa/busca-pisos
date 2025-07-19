#!/usr/bin/env python3
"""
Local development runner for inmobiliario-tools
This script helps start the application locally without Docker
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def check_requirements():
    """Check if required services are available"""
    print("🔍 Checking requirements...")
    
    # Check if PostgreSQL is running
    try:
        subprocess.run(["pg_isready", "-h", "localhost", "-p", "5432"], 
                      check=True, capture_output=True)
        print("✅ PostgreSQL is running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PostgreSQL is not running. Please start PostgreSQL on localhost:5432")
        print("   Create database: createdb inmobiliario_db")
        return False
    
    # Check if Redis is running
    try:
        subprocess.run(["redis-cli", "ping"], 
                      check=True, capture_output=True)
        print("✅ Redis is running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Redis is not running. Starting without caching...")
    
    return True

def setup_database():
    """Setup database if needed"""
    print("🗄️  Setting up database...")
    
    # Check if database exists
    try:
        result = subprocess.run(
            ["psql", "-h", "localhost", "-U", "inmobiliario_user", "-d", "inmobiliario_db", "-c", "SELECT 1;"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ Database exists")
            return True
    except FileNotFoundError:
        pass
    
    # Create database if it doesn't exist
    try:
        subprocess.run(
            ["createdb", "-h", "localhost", "-U", "inmobiliario_user", "inmobiliario_db"],
            check=True, capture_output=True
        )
        print("✅ Database created")
    except subprocess.CalledProcessError:
        print("⚠️  Could not create database, assuming it exists")
    
    return True

def install_dependencies():
    """Install Python and Node.js dependencies"""
    print("📦 Installing dependencies...")
    
    # Install backend dependencies
    backend_path = Path(__file__).parent / "backend"
    if (backend_path / "requirements.txt").exists():
        print("Installing Python dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      cwd=backend_path, check=True)
    
    # Install frontend dependencies
    frontend_path = Path(__file__).parent / "frontend"
    if (frontend_path / "package.json").exists():
        print("Installing Node.js dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_path, check=True)
    
    print("✅ Dependencies installed")

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting backend...")
    backend_path = Path(__file__).parent / "backend"
    
    env = os.environ.copy()
    env.update({
        "POSTGRES_USER": "inmobiliario_user",
        "POSTGRES_PASSWORD": "inmobiliario_pass", 
        "POSTGRES_DB": "inmobiliario_db",
        "SECRET_KEY": "dev-secret-key-change-in-production",
        "REDIS_URL": "redis://localhost:6379/0"
    })
    
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_path,
        env=env
    )

def start_frontend():
    """Start the Next.js frontend"""
    print("🎨 Starting frontend...")
    frontend_path = Path(__file__).parent / "frontend"
    
    return subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_path
    )

def start_celery():
    """Start Celery worker"""
    print("⚡ Starting Celery worker...")
    backend_path = Path(__file__).parent / "backend"
    
    env = os.environ.copy()
    env.update({
        "POSTGRES_USER": "inmobiliario_user",
        "POSTGRES_PASSWORD": "inmobiliario_pass",
        "POSTGRES_DB": "inmobiliario_db", 
        "SECRET_KEY": "dev-secret-key-change-in-production",
        "REDIS_URL": "redis://localhost:6379/0"
    })
    
    return subprocess.Popen(
        ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"],
        cwd=backend_path,
        env=env
    )

def main():
    """Main function to start the application locally"""
    print("🏠 Starting Inmobiliario Tools locally...")
    
    if not check_requirements():
        sys.exit(1)
    
    try:
        install_dependencies()
        setup_database()
        
        processes = []
        
        # Start backend
        backend_process = start_backend()
        processes.append(backend_process)
        time.sleep(3)  # Wait for backend to start
        
        # Start Celery (optional)
        try:
            celery_process = start_celery()
            processes.append(celery_process)
        except Exception as e:
            print(f"⚠️  Could not start Celery: {e}")
        
        # Start frontend
        frontend_process = start_frontend()
        processes.append(frontend_process)
        
        print("\n🎉 Application started successfully!")
        print("📱 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            for process in processes:
                process.terminate()
            
            # Wait for processes to terminate
            for process in processes:
                process.wait()
            
            print("✅ All services stopped")
    
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()