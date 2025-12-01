# SecurePath - Fraud Detection System

A comprehensive fraud detection system built with Django (backend) and React (frontend), featuring real-time transaction monitoring, ML-based risk scoring, and automated fraud detection.

## 🚀 Features

- **Real-time Transaction Monitoring**: Track and analyze transactions as they occur
- **ML-Based Fraud Detection**: Automated fraud scoring using machine learning
- **Bulk Upload**: Process large CSV files with transaction data
- **Audit Logging**: Complete audit trail of all system actions
- **Report Generation**: Export transaction reports in CSV and PDF formats
- **RESTful API**: Well-documented API with versioning support
- **Rate Limiting**: Built-in protection against API abuse
- **Responsive Dashboard**: Modern, mobile-friendly UI

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 15+ (recommended) or SQLite for development
- Redis 7+ (for Celery task queue)
- Docker & Docker Compose (optional, for containerized deployment)

## 🛠️ Installation

### Option 1: Local Development Setup

#### Backend Setup

```bash
cd securepath-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

#### Frontend Setup

```bash
cd securepath-dashboard

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm start
```

#### Start Celery Worker (Optional)

```bash
cd securepath-backend

# Start Redis (if not running)
redis-server

# Start Celery worker
celery -A backend worker -l info
```

### Option 2: Docker Setup

```bash
# From the root directory containing both projects
docker-compose up --build
```

This will start:
- PostgreSQL database on port 5432
- Redis on port 6379
- Django backend on port 8000
- Celery worker
- React frontend on port 3000

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in `securepath-backend/`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=securepath_db
DB_USER=your_db_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# API
API_TOKEN=your-secure-token

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Frontend Environment Variables

Create a `.env.local` file in `securepath-dashboard/`:

```env
REACT_APP_API_BASE_URL=http://localhost:8000/api
REACT_APP_API_TOKEN=your-secure-token
```

## 📚 API Documentation

### Authentication

All API endpoints (except `/status`) require Bearer token authentication:

```bash
Authorization: Bearer your-token-here
```

### Key Endpoints

- `GET /api/v1/status` - Health check
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/transactions` - Get paginated transactions
- `POST /api/v1/upload` - Upload transaction CSV file
- `POST /api/v1/detect-fraud` - Run fraud detection
- `GET /api/v1/audit-log` - Get audit logs
- `GET /api/v1/export/{type}` - Export reports (csv/pdf)

## 🧪 Testing

### Backend Tests

```bash
cd securepath-backend

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest api/tests/test_models.py
```

### Frontend Tests

```bash
cd securepath-dashboard

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## 🎨 Code Quality

### Backend

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
```

### Frontend

```bash
# Lint code
npm run lint

# Format code (if configured)
npm run format
```

## 📦 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in backend settings
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up HTTPS/SSL
- [ ] Configure CORS for production domains
- [ ] Set up proper logging
- [ ] Configure email backend
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

### Using Docker in Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

## 🔐 Security

- API authentication using Bearer tokens
- Rate limiting on all endpoints
- CSRF protection enabled
- SQL injection protection via Django ORM
- XSS protection with React
- Environment-based configuration
- Secure password hashing

## 📊 Database Migrations

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migrations
python manage.py showmigrations

# Rollback migration
python manage.py migrate api 0001_initial
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Django framework
- React and Create React App
- Lucide React for icons
- TailwindCSS for styling
