# Quick Start Guide

## Start Everything (One Command!)

```bash
docker-compose up --build -d
```

That's it! This command will:
- Pull PostgreSQL and Redis images
- Build the Django application
- Run database migrations automatically
- Collect static files
- Start all services (web, celery, flower)

## Check Status

```bash
# View all running containers
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f celery_worker
```

## Access the Application

- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **Flower (Celery)**: http://localhost:5555/

## Create Admin User

```bash
docker-compose exec web python manage.py createsuperuser
```

## Stop Everything

```bash
docker-compose down
```

## Reset Everything (Fresh Start)

```bash
# Stop and remove volumes (WARNING: deletes all data!)
docker-compose down -v

# Start fresh
docker-compose up --build -d
```

## Test OCR Upload

```bash
# Upload an image for OCR processing
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@your_image.png" \
  -F "language=eng"
```

## Troubleshooting

If something goes wrong:

```bash
# Check all logs
docker-compose logs

# Restart specific service
docker-compose restart web

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```
