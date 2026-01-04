@echo off
REM Complete Setup and Deployment Script for GPU OCR System (Windows)

echo ========================================
echo   GPU-Accelerated OCR System Setup
echo ========================================
echo.

REM Step 1: Check Python version
echo [1/8] Checking Python version...
python --version
echo.

REM Step 2: Create virtual environment
echo [2/8] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM Step 3: Activate virtual environment
echo [3/8] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Step 4: Upgrade pip
echo [4/8] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Step 5: Install dependencies (in stages)
echo [5/8] Installing dependencies...

echo Installing core Django packages...
pip install Django==4.2.8
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1
pip install python-decouple==3.8

echo Installing database drivers...
pip install psycopg2-binary==2.9.9

echo Installing Celery and Redis...
pip install celery==5.3.4
pip install redis==5.0.1
pip install django-celery-results==2.5.1
pip install django-celery-beat==2.5.0
pip install flower==2.0.1

echo Installing image processing libraries...
pip install Pillow==10.1.0
pip install numpy==1.24.3
pip install opencv-python-headless==4.8.1.78
pip install pdf2image==1.16.3

echo Installing GPU OCR libraries...
pip install easyocr==1.7.0
pip install torch>=2.0.0
pip install torchvision>=0.15.0

echo Installing server and utilities...
pip install gunicorn==21.2.0
pip install ipython==8.18.1

echo [OK] All dependencies installed
echo.

REM Step 6: Create .env file
echo [6/8] Creating .env file...
if not exist ".env" (
    copy .env.example .env
    echo [OK] .env file created from .env.example
    echo [WARNING] Please edit .env with your settings
) else (
    echo [OK] .env file already exists
)
echo.

REM Step 7: Run migrations
echo [7/8] Running database migrations...
python manage.py makemigrations
python manage.py migrate
echo [OK] Migrations completed
echo.

REM Step 8: Create superuser (optional)
echo [8/8] Create superuser (optional)
set /p create_super="Do you want to create a superuser? (y/n): "
if /i "%create_super%"=="y" (
    python manage.py createsuperuser
)
echo.

REM Check GPU availability
echo Checking GPU availability...
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env with your database credentials
echo 2. Start Docker services: docker-compose up -d
echo 3. Or run locally:
echo    - Terminal 1: python manage.py runserver
echo    - Terminal 2: celery -A ocr_project worker -l info
echo    - Terminal 3: celery -A ocr_project beat -l info
echo.
echo Access points:
echo - Django: http://localhost:8000/
echo - Admin: http://localhost:8000/admin/
echo - API: http://localhost:8000/api/
echo - Camera Status: http://localhost:8000/api/status/
echo - Flower: http://localhost:5555/
echo.
echo Happy OCR processing! 🚀
echo.
pause
