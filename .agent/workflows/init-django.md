---
description: Khởi tạo Django project với PostgreSQL và chạy development server
---

# Init Django Project & Setup PostgreSQL

Workflow để khởi tạo backend Django + DRF, cấu hình PostgreSQL (local/dev), migrations cơ bản và biến môi trường.

## Yêu cầu hệ thống
- Python 3.12+ (cho Django 6.0) hoặc Python 3.10+ (cho Django 5.2)
- Docker Desktop đã cài đặt và đang chạy
- Port 5432 khả dụng cho PostgreSQL

## Các bước thực hiện

### 1. Tạo Virtual Environment (nếu chưa có)
```powershell
python -m venv ./venv
```

// turbo
### 2. Kích hoạt Virtual Environment và cài Dependencies
```powershell
.\venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

// turbo
### 3. Khởi động PostgreSQL 16 bằng Docker
```powershell
docker-compose up -d
```

### 4. Chờ PostgreSQL sẵn sàng (khoảng 5-10 giây)
```powershell
docker-compose ps
```

// turbo
### 5. Chạy Database Migrations
```powershell
.\venv\Scripts\Activate.ps1; python manage.py migrate
```

### 6. Tạo Superuser (tuỳ chọn)
```powershell
.\venv\Scripts\Activate.ps1; python manage.py createsuperuser
```

// turbo
### 7. Chạy Development Server
```powershell
.\venv\Scripts\Activate.ps1; python manage.py runserver
```

## Kiểm tra kết quả

- **Admin Panel**: http://localhost:8000/admin/
- **Swagger API Docs**: http://localhost:8000/swagger/
- **ReDoc API Docs**: http://localhost:8000/redoc/

## Dừng Services

```powershell
# Dừng Django server: Ctrl+C trong terminal

# Dừng PostgreSQL container
docker-compose down

# Dừng và xoá data (reset database)
docker-compose down -v
```

## Biến môi trường (.env)

Tạo file `.env` từ `.env.example`:
```
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=voice_chat
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=localhost
DB_PORT=5432
```

## Troubleshooting

### Port 5432 đã được sử dụng
```powershell
# Kiểm tra process đang dùng port
netstat -ano | findstr :5432

# Hoặc đổi port trong docker-compose.yml thành 5433:5432
```

### Không kết nối được database
1. Kiểm tra Docker container đang chạy: `docker ps`
2. Kiểm tra logs: `docker logs voice_chat_db`
3. Đảm bảo file `.env` có đúng thông tin kết nối
