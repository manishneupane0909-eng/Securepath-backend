# api/views.py - FRONTEND INTEGRATION VERSION
from ninja import NinjaAPI, UploadedFile
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
import pandas as pd
import io
import time
import csv

from .models import Transaction

api = NinjaAPI(title="SecurePath FRDS API", version="1.0.0", auth=None)


# --- 1. UPLOAD ENDPOINT (Matches CsvUpload.js) ---
@api.post("/upload")
def upload_csv(request, file: UploadedFile):
    start = time.time()
    try:
        content = file.read().decode('utf-8', errors='ignore')
        df = pd.read_csv(io.StringIO(content), dtype=str)
        df = df.fillna('').astype(str)

        if df.empty:
            return {"status": "success", "records_uploaded": 0, "message": "Empty file"}

        total_rows = len(df)
        created = 0
        base_time = int(time.time())

        for idx, row in df.iterrows():
            unique_id = f"TXN_{base_time}_{idx}_{abs(hash(str(row.to_list()) + file.name)) & 0xFFFFFF}"

            if Transaction.objects.filter(transaction_id=unique_id).exists():
                continue

            try:
                amount_str = ''.join(filter(lambda x: x.isdigit() or x in '.,', str(row.get('amount', '') or '')))
                amount_val = float(amount_str.replace(',', '')) if amount_str else 0.0
            except:
                amount_val = 0.0

            date_val = timezone.now()
            try:
                date_str = str(row.get('date', '') or row.get('timestamp', '') or '')
                if date_str:
                    parsed = pd.to_datetime(date_str, errors='coerce')
                    if not pd.isna(parsed):
                        date_val = parsed
            except:
                pass

            merchant = str(row.get('merchant', '') or row.get('description', '') or 'Unknown Merchant')[:200]
            card = str(row.get('card', '') or row.get('card_number', '') or '****0000')[:19]
            country = str(row.get('country', '') or 'XX').upper()[:2]

            Transaction.objects.create(
                transaction_id=unique_id,
                amount=amount_val,
                date=date_val,
                merchant=merchant,
                card_number=card,
                ip_address='0.0.0.0',
                device_id='UPLOADED',
                country=country,
                currency='USD',
                status='pending',
                is_fraud=False
            )
            created += 1

        return {
            "status": "success",
            "records_uploaded": created,
            "message": f"Uploaded {created} records"
        }

    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}


# --- 2. DETECT ENDPOINT (Matches CsvUpload.js logic) ---
@api.post("/detect-fraud")
def detect_fraud(request):
    pending = Transaction.objects.filter(status='pending')
    flagged = 0
    updates = []

    for t in pending:
        score = 0.0
        # STRICT RULES (High Sensitivity)
        if t.amount > 10: score += 0.5
        if t.country in ['CN', 'RU', 'NG', 'BR', 'XX']: score += 0.4
        if 'UPLOADED' in t.device_id: score += 0.1

        t.fraud_score = min(score, 1.0)
        t.is_fraud = score >= 0.6

        if t.is_fraud:
            flagged += 1

        updates.append(t)

    if updates:
        Transaction.objects.bulk_update(updates, ['fraud_score', 'is_fraud'])

    return {
        "status": "success",
        "flagged": flagged,
        "processed": len(updates),
        "message": "Analysis Complete"
    }


# --- 3. NEW TRANSACTION LIST ENDPOINT (Matches App.js) ---
@api.get("/transactions")
def list_transactions(request):
    # We limit to top 500 riskiest/newest to prevent browser crash
    # Your frontend expects "risk_score" (0-100), but we have "fraud_score" (0.0-1.0)

    txns = Transaction.objects.all().order_by('-is_fraud', '-fraud_score', '-date')[:500]

    results = []
    for t in txns:
        results.append({
            "id": t.transaction_id,
            "transaction_id": t.transaction_id,
            "merchant": t.merchant,
            "amount": t.amount,
            "date": t.date.strftime("%Y-%m-%d %H:%M"),
            "country": t.country,

            # CRITICAL: Convert 0.9 -> 90 so your Dashboard turns RED
            "risk_score": int(t.fraud_score * 100),

            "status": "Review Needed" if t.is_fraud else "Approved",
            "is_fraud": t.is_fraud
        })

    return results


# --- 4. DASHBOARD STATS (Matches Dashboard.js logic) ---
@api.get("/dashboard/stats")
def stats(request):
    total = Transaction.objects.count()
    fraud = Transaction.objects.filter(is_fraud=True).count()
    return {
        "total_transactions": total,
        "fraud_detected": fraud
    }