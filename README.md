# ⚠️ This repository has been consolidated

**This backend-only repo is deprecated. The project has been moved to a monorepo structure.**

👉 **Go to the main repository:** [securepath](https://github.com/manishneupane0909-eng/securepath)

The main repo contains both the backend and frontend in a single repository for easier development and deployment.

---

# SecurePath - Fraud Detection System (Backend)

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
# Clone the main repository (not this one)
git clone https://github.com/manishneupane0909-eng/securepath.git
cd securepath/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

#### Frontend Setup

```bash
# From the main repository root
cd securepath/frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API endpoint

# Start development server
npm start
```

### Option 2: Docker Setup

```bash
# From the main repository root
cd securepath

# Build and start containers
docker-compose up --build

# The backend will be available at http://localhost:8000
# The frontend will be available at http://localhost:3000
```

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/securepath
REDIS_URL=redis://localhost:6379/0
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENV=sandbox
API_TOKEN=your-api-token-for-auth
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_PLAID_PUBLIC_KEY=your-plaid-public-key
```

## 📚 API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 License

This project is for educational purposes.
