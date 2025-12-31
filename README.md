# OCR Detector - Django Application

A scalable Django-based OCR (Optical Character Recognition) system that detects and extracts text and code from images and PDF documents, storing results in PostgreSQL.

## Features

- 📄 **Multi-format Support**: Process images (PNG, JPG, JPEG, GIF, BMP, TIFF) and PDF documents
- 🔍 **Advanced OCR**: Powered by Tesseract with image preprocessing for better accuracy
- 💻 **Code Detection**: Automatically identifies and extracts code blocks from OCR results
- 🚀 **Async Processing**: Celery-based background processing for scalability
- 📊 **RESTful API**: Complete REST API for document management
- 🐘 **PostgreSQL**: Robust database storage with indexing
- 🐳 **Docker Support**: Easy deployment with Docker Compose
- 📈 **Monitoring**: Flower dashboard for Celery task monitoring

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  Django API  │────▶│  PostgreSQL │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Redis     │────▶│   Celery    │
                    └──────────────┘     │   Workers   │
                                         └─────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │  Tesseract   │
                                        │     OCR      │
                                        └──────────────┘
```

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- At least 4GB RAM
- 2GB free disk space

**Note**: You don't need Python, PostgreSQL, or any other dependencies installed locally - Docker handles everything!

## Quick Start

### 1. Clone and Setup

```bash
cd c:\Users\rauna\OneDrive\Desktop\ocr
```

### 2. Start Everything (One Command!)

**Windows:**
```bash
start.bat
```

**Or manually:**
```bash
docker-compose up --build -d
```

That's it! The system will:
✅ Pull PostgreSQL and Redis images
✅ Build Django application  
✅ Run database migrations automatically
✅ Collect static files
✅ Start web server, Celery workers, and monitoring

### 3. Create Admin User (Optional)

```bash
docker-compose exec web python manage.py createsuperuser
```

### 4. Access the Application

- **API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Flower (Celery Monitoring)**: http://localhost:5555/

## API Endpoints

### Document Management

#### Upload Document
```bash
POST /api/documents/upload/
Content-Type: multipart/form-data

Parameters:
- file: Image or PDF file
- language: OCR language code (default: 'eng')

Example:
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@image.png" \
  -F "language=eng"
```

#### List Documents
```bash
GET /api/documents/

Query Parameters:
- status: Filter by status (pending, processing, completed, failed)
- order_by: Sort field (default: -uploaded_at)

Example:
curl http://localhost:8000/api/documents/?status=completed
```

#### Get Document Details
```bash
GET /api/documents/{id}/

Example:
curl http://localhost:8000/api/documents/123e4567-e89b-12d3-a456-426614174000/
```

#### Get Document Results
```bash
GET /api/documents/{id}/results/

Example:
curl http://localhost:8000/api/documents/123e4567-e89b-12d3-a456-426614174000/results/
```

#### Get Detected Code Blocks
```bash
GET /api/documents/{id}/code_blocks/

Example:
curl http://localhost:8000/api/documents/123e4567-e89b-12d3-a456-426614174000/code_blocks/
```

#### Reprocess Document
```bash
POST /api/documents/{id}/reprocess/

Body:
{
  "language": "eng"
}
```

#### Delete Document
```bash
DELETE /api/documents/{id}/
```

### OCR Results

#### List All Results
```bash
GET /api/results/

Query Parameters:
- document: Filter by document ID
- content_type: Filter by type (text, code, mixed)

Example:
curl http://localhost:8000/api/results/?content_type=code
```

#### Get Result Details
```bash
GET /api/results/{id}/
```

### Code Blocks

#### List Code Blocks
```bash
GET /api/code-blocks/

Query Parameters:
- language: Filter by programming language
- document: Filter by document ID

Example:
curl http://localhost:8000/api/code-blocks/?language=python
```

## Configuration

### Environment Variables

Key settings in `.env`:

```env
# Database
DB_NAME=ocr_db
DB_USER=ocr_user
DB_PASSWORD=ocr_password
DB_HOST=db
DB_PORT=5432

# OCR Settings
OCR_MAX_FILE_SIZE=10485760  # 10MB in bytes
OCR_LANGUAGES=eng  # Comma-separated language codes

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
```

### Supported Languages

By default, only English ('eng') is supported. To add more languages:

1. Update the Dockerfile to install additional Tesseract language packs:
```dockerfile
RUN apt-get install -y tesseract-ocr-fra tesseract-ocr-deu
```

2. Update OCR_LANGUAGES in `.env`:
```env
OCR_LANGUAGES=eng,fra,deu
```

## DLocal Development with Docker

The `.env` file is already configured for Docker. Just run:

```bash
docker-compose up --build -d
```

All services will start automatically with hot-reloading enabled.ery -A ocr_project worker -l info
celery -A ocr_project beat -l info
```

### Running Tests

```bash
# Run tests
docker-compose exec web python manage.py test

# With coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

## Scaling

### Horizontal Scaling

Scale Celery workers:
```bash
docker-compose up -d --scale celery_worker=4
```

### Performance Optimization

1. **Database Indexing**: Models include indexes on frequently queried fields
2. **Celery Concurrency**: Adjust `--concurrency` in docker-compose.yml
3. **Image Preprocessing**: Customize preprocessing in `services.py`
4. **Caching**: Add Redis caching for API responses

## Monitoring

### Celery Tasks

Access Flower dashboard at http://localhost:5555/ to monitor:
- Active tasks
- Task history
- Worker status
- Task execution time

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
```

### Database

```bash
# Access PostgreSQL
docker-compose exec db psql -U ocr_user -d ocr_db

# View documents
SELECT filename, status, uploaded_at FROM ocr_app_ocrdocument;
```

## Troubleshooting

### Issue: OCR processing fails

**Solution**: Check Celery worker logs:
```bash
docker-compose logs celery_worker
```

### Issue: Database connection error

**Solution**: Ensure PostgreSQL is healthy:
```bash
docker-compose ps
docker-compose exec db pg_isready -U ocr_user
```

### Issue: Out of memory

**Solution**: Reduce Celery concurrency or add more resources:
```yaml
# docker-compose.yml
celery_worker:
  command: celery -A ocr_project worker --loglevel=info --concurrency=2
```

### Issue: Tesseract not found

**Solution**: Rebuild Docker image:
```bash
docker-compose build --no-cache web
docker-compose up -d
```

## Project Structure

```
ocr/
├── docker-compose.yml       # Docker orchestration
├── Dockerfile              # Docker image definition
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── .env                   # Environment variables
├── ocr_project/           # Django project settings
│   ├── settings.py        # Main settings
│   ├── urls.py           # URL routing
│   ├── celery.py         # Celery configuration
│   └── wsgi.py           # WSGI application
└── ocr_app/              # Main application
    ├── models.py         # Database models
    ├── views.py          # API views
    ├── serializers.py    # DRF serializers
    ├── services.py       # OCR service logic
    ├── tasks.py          # Celery tasks
    ├── urls.py           # App URLs
    └── admin.py          # Admin configuration
```

## Models

### OCRDocument
- Stores uploaded document metadata
- Tracks processing status
- Links to OCR results

### OCRResult
- Stores extracted text per page
- Content type classification
- Confidence scores

### CodeBlock
- Detected code snippets
- Programming language identification
- Line number tracking

### ProcessingLog
- Audit trail for processing
- Error logging
- Performance metrics

## Security Considerations

1. **File Upload Validation**: Size and type restrictions
2. **Input Sanitization**: Validated through DRF serializers
3. **Database**: Connection pooling and prepared statements
4. **Docker**: Non-root user in container
5. **Secrets**: Use environment variables, never commit .env

## Future Enhancements

- [ ] Batch processing for multiple files
- [ ] Webhook notifications
- [ ] S3/cloud storage integration
- [ ] Advanced code syntax validation
- [ ] Machine learning for better language detection
- [ ] Real-time processing with WebSockets
- [ ] Export results to various formats
- [ ] OCR quality scoring

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the logs: `docker-compose logs -f`
- Review Celery tasks in Flower: http://localhost:5555/

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

Built with ❤️ using Django, Tesseract, PostgreSQL, and Celery
