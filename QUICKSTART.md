# Quick Start Guide - Real-Time OCR Camera System

## ⚡ ONE COMMAND START!

### Windows:
```bash
start.bat
```

### Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

## 🎯 What You Get

The system **automatically**:
1. ✅ Starts your camera
2. ✅ Enhances video in real-time (deblurs, sharpens)
3. ✅ Detects text and code as it appears
4. ✅ Auto-captures when text/code detected
5. ✅ Processes through OCR pipeline
6. ✅ Stores results in PostgreSQL

## 🌐 Access Points

- **📹 Live Camera**: http://localhost:8000/api/live/
- **🔌 API**: http://localhost:8000/api/
- **👤 Admin**: http://localhost:8000/admin/
- **📊 Celery Monitor**: http://localhost:5555/

## 📸 How to Use

1. **Start the system** (run `start.bat`)
2. **Open your browser** to http://localhost:8000/api/live/
3. **Point camera** at text or code
4. **Watch it detect automatically!**

The system will:
- Show live camera feed with statistics
- Automatically detect and capture text/code
- Process captures in background
- Store results in database

## 🎛️ Configuration

Edit `.env` file before starting:

```env
# Auto-start camera
AUTO_START_CAMERA=True

# Camera device (0=default, 1=second camera)
CAMERA_ID=0
```

## ⚙️ Manual Controls

## ⚙️ Manual Controls

Create admin user:
```bash
docker-compose exec web python manage.py createsuperuser
```
🎨 Features

**Real-Time Enhancement:**
- Deblurring and sharpening
- Contrast enhancement
- Auto brightness adjustment

**Smart Detection:**
- Text confidence scoring
- Code pattern recognition (Python, JavaScript, Java, etc.)
- Auto-capture on detection

**Processing:**
- Background OCR via Celery
- Multi-language support
- Code block extraction

## 🚀 API Examples

Upload image manually:
```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@image.png" \
  -F "language=eng"
```

Get live camera stats:
```bash
curl http://localhost:8000/api/video/stats/
```

Process captured frames:
```bash
curl -X POST http://localhost:8000/api/video/process-captures/
```

## 📚 Full Documentation

- **Camera Guide**: See [CAMERA_GUIDE.md](CAMERA_GUIDE.md)
- **Full README**: See [README.md](README.md)

## 🆘 Troubleshooting

**Camera not working?**
- On Windows: May need to run locally without Docker
- Check camera permissions
- Try different CAMERA_ID value

**Low detection rate?**
- Improve lighting
- Hold text/code steady
- Adjust camera distance

**Performance issues?**
- Lower camera resolution in `video_capture.py`
- Reduce Celery workers
- Increase detection cooldown

---

🎉 **That's it! Your real-time OCR system is ready!**
```bash
# Check all logs
docker-compose logs

# Restart specific service
docker-compose restart web

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```
