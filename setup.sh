#!/bin/bash
# Complete Setup and Deployment Script for GPU OCR System

echo "========================================"
echo "  GPU-Accelerated OCR System Setup"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo -e "${YELLOW}[1/8] Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
echo ""

# Step 2: Create virtual environment
echo -e "${YELLOW}[2/8] Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi
echo ""

# Step 3: Activate virtual environment
echo -e "${YELLOW}[3/8] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 4: Upgrade pip
echo -e "${YELLOW}[4/8] Upgrading pip...${NC}"
pip install --upgrade pip
echo ""

# Step 5: Install dependencies (in stages to avoid build conflicts)
echo -e "${YELLOW}[5/8] Installing dependencies...${NC}"

echo "Installing core Django packages..."
pip install Django==4.2.8
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1
pip install python-decouple==3.8

echo "Installing database drivers..."
pip install psycopg2-binary==2.9.9

echo "Installing Celery and Redis..."
pip install celery==5.3.4
pip install redis==5.0.1
pip install django-celery-results==2.5.1
pip install django-celery-beat==2.5.0
pip install flower==2.0.1

echo "Installing image processing libraries..."
pip install Pillow==10.1.0
pip install numpy==1.24.3
pip install opencv-python-headless==4.8.1.78
pip install pdf2image==1.16.3

echo "Installing GPU OCR libraries..."
pip install easyocr==1.7.0
pip install torch>=2.0.0
pip install torchvision>=0.15.0

echo "Installing server and utilities..."
pip install gunicorn==21.2.0
pip install python-magic==0.4.27
pip install ipython==8.18.1

echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Step 6: Create .env file
echo -e "${YELLOW}[6/8] Creating .env file...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from .env.example${NC}"
    echo -e "${YELLOW}⚠ Please edit .env with your settings${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# Step 7: Run migrations
echo -e "${YELLOW}[7/8] Running database migrations...${NC}"
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Step 8: Create superuser (optional)
echo -e "${YELLOW}[8/8] Create superuser (optional)${NC}"
read -p "Do you want to create a superuser? (y/n): " create_super
if [ "$create_super" = "y" ]; then
    python manage.py createsuperuser
fi
echo ""

# Check GPU availability
echo -e "${YELLOW}Checking GPU availability...${NC}"
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
echo ""

echo "========================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env with your database credentials"
echo "2. Start Docker services: docker-compose up -d"
echo "3. Or run locally:"
echo "   - Terminal 1: python manage.py runserver"
echo "   - Terminal 2: celery -A ocr_project worker -l info"
echo "   - Terminal 3: celery -A ocr_project beat -l info"
echo ""
echo "Access points:"
echo "- Django: http://localhost:8000/"
echo "- Admin: http://localhost:8000/admin/"
echo "- API: http://localhost:8000/api/"
echo "- Camera Status: http://localhost:8000/api/status/"
echo "- Flower: http://localhost:5555/"
echo ""
echo "Happy OCR processing! 🚀"
