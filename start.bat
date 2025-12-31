@echo off
cls
echo ========================================
echo   OCR REAL-TIME CAMERA SYSTEM
echo ========================================
echo.
echo This will start:
echo   - PostgreSQL database
echo   - Redis message queue
echo   - Django web server
echo   - Real-time camera OCR detection
echo   - Celery workers
echo   - Monitoring dashboard
echo.
echo ========================================
echo.

echo [1/4] Stopping any existing containers...
docker-compose down 2>nul

echo.
echo [2/4] Building Docker images...
docker-compose build

echo.
echo [3/4] Starting all services...
docker-compose up -d

echo.
echo [4/4] Waiting for services to initialize...
timeout /t 20 /nobreak > nul

echo.
echo ========================================
echo   SYSTEM STATUS
echo ========================================
docker-compose ps

echo.
echo ========================================
echo   🎉 YOUR SYSTEM IS READY!
echo ========================================
echo.
echo   📹 Live Camera:  http://localhost:8000/api/live/
echo   🔌 API:          http://localhost:8000/api/
echo   👤 Admin:        http://localhost:8000/admin/
echo   📊 Monitor:      http://localhost:5555/
echo.
echo ========================================
echo.
echo The camera will start AUTOMATICALLY!
echo Just open: http://localhost:8000/api/live/
echo.
echo To create admin user:
echo   docker-compose exec web python manage.py createsuperuser
echo.
echo To view logs:
echo   docker-compose logs -f web
echo.
echo To stop:
echo   docker-compose down
echo.
pause
