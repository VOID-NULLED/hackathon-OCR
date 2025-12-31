@echo off
echo ========================================
echo   OCR Detector - Docker Setup
echo ========================================
echo.

echo Stopping any existing containers...
docker-compose down

echo.
echo Building and starting all services...
docker-compose up --build -d

echo.
echo Waiting for services to be healthy...
timeout /t 15 /nobreak > nul

echo.
echo ========================================
echo   Services Status
echo ========================================
docker-compose ps

echo.
echo ========================================
echo   Your OCR System is Ready!
echo ========================================
echo.
echo   API:       http://localhost:8000/api/
echo   Admin:     http://localhost:8000/admin/
echo   Flower:    http://localhost:5555/
echo.
echo ========================================
echo.
echo To create an admin user, run:
echo   docker-compose exec web python manage.py createsuperuser
echo.
echo To view logs, run:
echo   docker-compose logs -f
echo.
echo To stop all services, run:
echo   docker-compose down
echo.
pause
