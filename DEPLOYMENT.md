# Production Deployment Guide for Ubuntu Server

## 🚀 Quick Start for Maximum Performance

### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip wkhtmltopdf libmagic1

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Performance Configuration
```bash
# Copy and customize environment variables
cp .env.example .env
nano .env  # Adjust values based on your server specs

# For 16-core server with 64GB RAM:
echo "UVICORN_WORKERS=16" >> .env
echo "MAX_WORKERS=256" >> .env
echo "PROCESS_POOL_SIZE=32" >> .env
echo "MAX_CONCURRENT_OPERATIONS=128" >> .env

# Load environment variables
export $(cat .env | xargs)
```

### 3. Production Startup
```bash
# Start with optimized settings
python main.py --host 0.0.0.0 --port 8000 --workers 16

# Or use systemd service (recommended)
sudo nano /etc/systemd/system/pdf-converter.service
```

### 4. Nginx Reverse Proxy (Recommended)
```nginx
# /etc/nginx/sites-available/pdf-converter
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings for large file uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        client_max_body_size 500M;
    }
}
```

### 5. Monitoring Performance
```bash
# Check running processes
ps aux | grep python

# Monitor CPU and memory usage
htop

# Check application logs
tail -f /var/log/pdf-converter.log
```

## ⚡ Performance Tuning

### For High-Traffic Servers:
- **32+ CPU cores**: Set UVICORN_WORKERS=32, PROCESS_POOL_SIZE=64
- **128GB+ RAM**: MAX_CONCURRENT_OPERATIONS=256
- **NVMe storage**: Faster file I/O operations

### Memory Considerations:
- Each worker process uses ~200-500MB RAM
- Process pool adds ~100MB per process
- Monitor with `free -h` and adjust accordingly

### Scaling Horizontally:
- Use load balancer (nginx upstream)
- Multiple server instances
- Redis for session storage (future enhancement)