# Django OCR Real-Time Camera System

A scalable Django-based OCR system with real-time camera monitoring, automatic text/code detection, video enhancement, and Docker deployment.

## Quick Start

```bash
# Start everything
start.bat

# Access the system
Browser: http://localhost:8000/api/live/
API: http://localhost:8000/api/
Flower: http://localhost:5555
```

## Features

### Real-Time Camera OCR
- **Auto-Start**: Camera starts automatically on system boot
- **Live Monitoring**: Continuous video stream analysis
- **Smart Detection**: Identifies text/code with 65% confidence threshold
- **Auto-Capture**: Captures and processes detected content automatically
- **Cooldown**: 2-second delay between captures to prevent duplicates

### Video Enhancement
- **Deblurring**: Bilateral filtering for noise reduction
- **Sharpening**: Unsharp mask for clarity improvement
- **Contrast**: CLAHE (Contrast Limited Adaptive Histogram Equalization)
- **Real-Time**: All processing happens during live capture

### OCR Processing
- **Text Extraction**: Tesseract OCR with preprocessing
- **Code Detection**: Identifies and extracts code blocks
- **Async Processing**: Celery background tasks
- **Result Storage**: PostgreSQL database with full history

## Configuration

Edit `.env` file:

```env
# Camera Settings
AUTO_START_CAMERA=True    # Start camera on boot
CAMERA_ID=0               # Camera device index (0=default)

# OCR Settings
OCR_CONFIDENCE_THRESHOLD=65.0
OCR_CAPTURE_COOLDOWN=2.0
OCR_MAX_FILE_SIZE=10485760

# Database
POSTGRES_DB=ocr_db
POSTGRES_USER=ocr_user
POSTGRES_PASSWORD=your_secure_password
```

## API Endpoints

### Camera Control
```bash
# View live feed
GET http://localhost:8000/api/live/

# Camera stats
GET http://localhost:8000/api/camera/stats/

# Start/stop camera
POST http://localhost:8000/api/camera/start/
POST http://localhost:8000/api/camera/stop/

# View captures
GET http://localhost:8000/api/camera/captures/
```

### OCR Operations
```bash
# Upload for OCR
POST http://localhost:8000/api/ocr/upload/
Content-Type: multipart/form-data
Body: file=@image.jpg

# List documents
GET http://localhost:8000/api/ocr/documents/

# Get results
GET http://localhost:8000/api/ocr/documents/{id}/results/

# Get code blocks
GET http://localhost:8000/api/ocr/code-blocks/
```

## Project Structure

```
ocr/
├── docker-compose.yml      # 6 services: db, redis, web, celery, flower
├── Dockerfile              # Python 3.11 + Tesseract + OpenCV
├── entrypoint.sh          # Auto migrations and setup
├── start.bat              # One-command startup
├── requirements.txt       # Python dependencies
├── .env                   # Configuration
├── manage.py             # Django management
├── ocr_project/
│   ├── settings.py       # Django + Camera config
│   ├── celery.py         # Async task setup
│   └── urls.py           # URL routing
└── ocr_app/
    ├── models.py         # OCRDocument, OCRResult, CodeBlock
    ├── video_capture.py  # Camera + Enhancement + Detection
    ├── video_views.py    # Streaming + Control endpoints
    ├── services.py       # OCR processing logic
    ├── tasks.py          # Celery async tasks
    └── templates/
        └── live_camera.html  # Web UI
```

## Docker Services

1. **db**: PostgreSQL 15 (port 5432)
2. **redis**: Redis 7 (port 6379)
3. **web**: Django + Gunicorn (port 8000)
4. **celery_worker**: Background OCR processing
5. **celery_beat**: Scheduled tasks
6. **flower**: Celery monitoring (port 5555)

## Troubleshooting

### Camera Access Issues
**Windows**: Camera works natively
**Linux**: Add to docker-compose.yml web service:
```yaml
devices:
  - /dev/video0:/dev/video0
privileged: true
```

### Port Already in Use
```bash
docker-compose down
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Connection Failed
```bash
docker-compose down -v
docker-compose up -d db
# Wait 10 seconds
docker-compose up
```

### OCR Not Detecting Text
- Ensure text is clear and well-lit
- Increase confidence threshold in .env (lower = more sensitive)
- Check camera stats: `http://localhost:8000/api/camera/stats/`
- View captures: `http://localhost:8000/api/camera/captures/`

### Container Logs
```bash
docker-compose logs web
docker-compose logs celery_worker
docker-compose logs -f  # Follow all logs
```

## Tech Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Database**: PostgreSQL 15
- **Task Queue**: Celery 5.3.4 + Redis 7
- **OCR**: Tesseract + pytesseract
- **Video**: OpenCV (opencv-python-headless)
- **Deployment**: Docker + Docker Compose
- **Server**: Gunicorn
- **Monitoring**: Flower

## Development

### Manual Setup (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: apt-get install tesseract-ocr

# Run migrations
python manage.py migrate

# Start services
python manage.py runserver
celery -A ocr_project worker -l info
celery -A ocr_project beat -l info
```

### Environment Variables
All configuration in `.env` file - never commit with real credentials.

## License

MIT License - use freely for your projects.
