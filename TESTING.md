# Testing & Verification Guide

## Quick Test Commands

```bash
# Test 1: Check GPU detection
python -c "import torch; print(f'GPU: {torch.cuda.is_available()}')"

# Test 2: Test EasyOCR initialization
python -c "import easyocr; reader = easyocr.Reader(['en']); print('EasyOCR ready!')"

# Test 3: Test database connection
python manage.py check

# Test 4: Test Celery connection
celery -A ocr_project inspect ping

# Test 5: Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print(f'Camera: {cap.isOpened()}'); cap.release()"
```

## Manual Testing Steps

### 1. Setup Verification
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 2. Start Services
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A ocr_project worker -l info

# Terminal 3: Celery Beat
celery -A ocr_project beat -l info
```

### 3. Test Camera System
```bash
# Check camera status
curl http://localhost:8000/api/status/

# Expected output:
{
  "total_frames": 0,
  "enhanced_frames": 0,  
  "detected_text": 0,
  "auto_captures": 0,
  "fps": 0,
  "running": true
}
```

### 4. Test OCR Upload
```bash
# Upload a test image
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@test_image.png" \
  -F "language=eng"

# Expected output:
{
  "document": {...},
  "task_id": "abc-123",
  "message": "Document uploaded successfully..."
}
```

### 5. Check FrameMetadata
```bash
# Access Django admin
http://localhost:8000/admin/

# Navigate to: OCR App > Frame Metadata
# Should see captured frames with metrics
```

### 6. Test GPU OCR
```python
# Run in Python shell
python manage.py shell

from ocr_app.gpu_services import get_gpu_ocr_service
import cv2

# Initialize service
gpu_ocr = get_gpu_ocr_service()
print(f"GPU Enabled: {gpu_ocr.use_gpu}")

# Test on sample image
result = gpu_ocr.process_image('path/to/test.png')
print(result)  # Should show text, confidence, blur_variance, etc.
```

## Scalability Tests

### Load Testing
```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << EOF
from locust import HttpUser, task

class OCRUser(HttpUser):
    @task
    def get_status(self):
        self.client.get("/api/status/")
    
    @task
    def upload_document(self):
        files = {'file': open('test.png', 'rb')}
        self.client.post("/api/documents/upload/", files=files)
EOF

# Run load test
locust -f locustfile.py
# Open http://localhost:8089
```

### Database Performance
```sql
-- Test query performance
EXPLAIN ANALYZE 
SELECT * FROM frame_metadata 
WHERE camera = 'camera_0' 
AND blur_var > 200 
ORDER BY timestamp DESC 
LIMIT 100;

-- Should use indexes, execution time < 10ms
```

### Celery Performance
```python
# Test concurrent task processing
from ocr_app.tasks import process_ocr_task
import time

# Queue 100 tasks
start = time.time()
task_ids = []
for i in range(100):
    task = process_ocr_task.delay(document_id, 'eng')
    task_ids.append(task.id)

# Check completion
time.sleep(30)
completed = sum(1 for tid in task_ids if AsyncResult(tid).ready())
print(f"Completed: {completed}/100 in 30s")
```

## Production Readiness Checklist

### Security
- [ ] DEBUG=False in .env
- [ ] Strong SECRET_KEY generated
- [ ] ALLOWED_HOSTS configured
- [ ] HTTPS/SSL enabled
- [ ] Database passwords secure
- [ ] File upload validation active
- [ ] Rate limiting configured

### Performance
- [ ] Database indexes created (auto via migrations)
- [ ] Connection pooling enabled (CONN_MAX_AGE=600)
- [ ] Celery workers scaled (--concurrency=8)
- [ ] Redis persistence configured
- [ ] Static files collected
- [ ] Media storage configured (S3/cloud)

### Monitoring
- [ ] Logging configured (logs/django.log)
- [ ] Flower dashboard accessible
- [ ] Error tracking (Sentry recommended)
- [ ] Database monitoring
- [ ] GPU utilization tracking

### Backup
- [ ] Database backup strategy
- [ ] Media files backup
- [ ] Configuration backup (.env)
- [ ] Migration backups

### Documentation
- [ ] README.md complete ✓
- [ ] API documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide

## Known Issues & Solutions

### Issue: psycopg2-binary build error
**Solution**: Use Docker or install `psycopg2` instead
```bash
pip install psycopg2  # May need PostgreSQL dev libraries
```

### Issue: EasyOCR model download slow
**Solution**: Download models manually
```python
import easyocr
reader = easyocr.Reader(['en'], download_enabled=True)
```

### Issue: Camera not working in Docker
**Solution**: Run Django locally for camera access
```bash
# Stop Docker web service
docker-compose stop web

# Run Django locally
python manage.py runserver
```

### Issue: GPU out of memory
**Solution**: Reduce batch size or use CPU
```python
# In gpu_services.py
self.reader = easyocr.Reader(['en'], gpu=False)  # Force CPU
```

## Success Criteria

✅ System fully integrated and tested when:

1. **GPU Detection**: System logs show GPU detected (or CPU fallback)
2. **Camera Running**: `/api/status/` returns `running: true`
3. **Migrations Applied**: FrameMetadata table exists in database
4. **OCR Processing**: Upload test returns task_id and processes successfully  
5. **Analytics Working**: FrameMetadata records created with metrics
6. **Celery Active**: Tasks complete within expected time
7. **Admin Access**: Can view all models in admin panel
8. **No Errors**: No critical errors in logs

## Final Validation

```bash
# Run all tests
python manage.py test

# Check system health
curl http://localhost:8000/api/health/

# View recent captures
curl http://localhost:8000/api/documents/?order_by=-uploaded_at

# Check analytics data
psql -U ocr_user -d ocr_db -c "SELECT COUNT(*) FROM frame_metadata;"
```

**System is production-ready when all checks pass! 🚀**
