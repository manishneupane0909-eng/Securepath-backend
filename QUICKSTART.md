# 🚀 Quick Start Guide

## Running SecurePath - Simple Steps

### 1️⃣ Start Backend (Terminal 1)

```bash
cd securepath-backend

# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start server
python manage.py runserver
```

✅ Backend runs at: **http://localhost:8000**

---

### 2️⃣ Start Frontend (Terminal 2 - NEW WINDOW)

```bash
cd securepath-dashboard

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

✅ Frontend runs at: **http://localhost:3000**

---

### 3️⃣ Open Browser

Go to **http://localhost:3000** and you'll see the dashboard!

---

## 🎯 Quick Test

1. Upload a CSV file with transactions
2. Click "Run Fraud Detection"
3. View results in the dashboard

---

## Sample CSV Format

```csv
transaction_id,amount,date,merchant,card_number
TXN001,150.00,2024-12-01 10:30:00,Amazon,1234567890123456
TXN002,6500.00,2024-12-01 11:00:00,Suspicious Store,9876543210987654
```

---

## 🔧 If Something Breaks

**Backend errors?**
```bash
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

**Frontend errors?**
```bash
npm install
npm start
```
