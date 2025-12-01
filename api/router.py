# api/router.py - COMPLETE FINAL VERSION (Optimized for Speed)
from ninja import Router, File, UploadedFile
from api.auth import auth_bearer, token_query_auth
import pandas as pd
import os
import io  # Used for reading CSV into memory
import csv  # For generating CSV export
from django.db.models import Sum, Count, F, Q
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
import gzip  # Kept for potential decompression logic

# Import the Transaction and AuditLog models
from api.models import Transaction, SystemMetrics, AuditLog

router = Router()


@router.get("/status", auth=None)
def status(request):
    """Returns the API status to confirm the backend is running."""
    return {"status": "ok", "message": "API is alive"}


@router.get("/dashboard/stats", auth=auth_bearer)
def stats(request):
    """Returns high-level statistics by querying the Transaction model."""
    total_txns = Transaction.objects.count()

    aggregation = Transaction.objects.aggregate(
        total_amount=Sum('amount'),
        fraud_count=Count('pk', filter=Q(is_fraud=True)),
        pending_count=Count('pk', filter=Q(status='pending'))
    )

    return {
        "total_transactions": total_txns,
        "fraud_detected": aggregation['fraud_count'] or 0,
        "pending_review": aggregation['pending_count'] or 0,
        "total_amount": float(aggregation['total_amount'] or 0)
    }


@router.get("/dashboard/transactions", auth=auth_bearer)
def transactions(request, page: int = 1, page_size: int = 10):
    """Returns a paginated list of recent transactions."""
    offset = (page - 1) * page_size
    limit = page_size

    txns = Transaction.objects.all().order_by('-date')[offset:offset + limit]

    txn_list = [{
        "transaction_id": txn.transaction_id,
        "amount": float(txn.amount),
        "merchant": txn.merchant,
        "status": txn.status,
        "fraud_score": float(txn.fraud_score or 0.0),
        "is_fraud": txn.is_fraud,
    } for txn in txns]

    return {"transactions": txn_list, "total": Transaction.objects.count()}


@router.get("/audit-log", auth=auth_bearer)
def audit_log(request, page: int = 1, page_size: int = 20):
    """Returns a paginated list of system actions from the AuditLog model."""
    offset = (page - 1) * page_size
    limit = page_size

    logs = AuditLog.objects.all().order_by('-timestamp')[offset:offset + limit]

    log_list = [{
        "action": log.action,
        "transaction_id": log.transaction_id,
        "details": log.details,
        "user": log.user,
        "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
    } for log in logs]

    return {"logs": log_list, "total": AuditLog.objects.count()}


@router.post("/detect-fraud", auth=auth_bearer)
def detect_fraud(request):
    """
    Massively optimized fraud detection using only bulk updates (no Python looping).
    This resolves the slowness issue for large datasets.
    """
    start_time = timezone.now()
    HIGH_RISK_AMOUNT = Decimal('5000.00')
    HIGH_SCORE = Decimal('0.5')

    # 1. Identify all transactions needing processing
    transactions_to_process = Transaction.objects.filter(
        Q(status='pending') | Q(status='review')
    )
    processed_count = transactions_to_process.count()

    # 2. Bulk Update: Identify and REJECT/FLAG high-risk transactions (Rule 1: High Amount)

    # Filter for high-risk amount among transactions needing processing
    high_risk_txns = transactions_to_process.filter(amount__gte=HIGH_RISK_AMOUNT)
    fraud_count = high_risk_txns.count()

    # Update high-risk transactions
    high_risk_txns.update(
        is_fraud=True,
        fraud_score=HIGH_SCORE,
        fraud_reasons='High transaction amount (>= $5000).',
        status='rejected'
    )

    # 3. Bulk Update: APPROVE remaining transactions

    # Select all transactions that were NOT flagged in the previous step
    transactions_to_approve = transactions_to_process.exclude(is_fraud=True)

    # Update safe transactions
    transactions_to_approve.update(
        is_fraud=False,
        fraud_score=Decimal('0.0'),
        fraud_reasons='',
        status='approved'
    )

    fraud_detected_count = fraud_count

    # 4. Log the action
    AuditLog.objects.create(
        action="Fraud Detection Run (Bulk Optimized)",
        details=f"Processed {processed_count} transactions via 3 SQL queries. Detected {fraud_detected_count} fraud attempts.",
        user="SYSTEM",
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    duration = (timezone.now() - start_time).total_seconds()

    return {
        "status": "success",
        "message": f"Detection complete. {processed_count} processed in {round(duration, 3)}s.",
        "transactions_processed": processed_count,
        "fraud_detected": fraud_detected_count,
        "duration_seconds": round(duration, 3)
    }


@router.get("/export/{type}", auth=token_query_auth)
def export_report(request, type: str):
    """Generates and returns a report (CSV or PDF) of all transactions."""
    if type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Amount', 'Date', 'Merchant', 'Is Fraud', 'Status', 'Score'])

        for txn in Transaction.objects.all().iterator():
            writer.writerow([
                txn.transaction_id,
                txn.amount,
                txn.date.strftime('%Y-%m-%d %H:%M:%S'),
                txn.merchant,
                'YES' if txn.is_fraud else 'NO',
                txn.status,
                txn.fraud_score
            ])

        return response

    elif type == 'pdf':
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transactions_report.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        p.drawString(100, 750, "SecurePath Fraud Detection Report")
        p.drawString(100, 710, f"Total Transactions: {Transaction.objects.count()}")
        p.drawString(100, 690, f"Report Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")

        p.showPage()
        p.save()
        return response

    return {"error": f"Unsupported export type: {type}"}


@router.post("/upload", auth=auth_bearer)
def upload_file(request, file: UploadedFile = File(...)):
    """
    Handles file upload: Synchronously processes the file into the database.
    (Used for small files to avoid Celery complexity).
    """
    file_name = file.name

    try:
        # 1. Read the file content (synchronous)
        file_data = file.read()

        # 2. Read the content into a DataFrame
        df = pd.read_csv(io.BytesIO(file_data))
        initial_rows = len(df)

        # 3. Clean/Normalize DataFrame column names
        df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
        df.rename(columns={'txn_id': 'transaction_id', 'txn_date': 'date'}, inplace=True)

        # 4. Prepare data for bulk insert
        transactions_to_create = []
        for index, row in df.iterrows():
            # Safely handle the date column
            try:
                date_val = pd.to_datetime(row.get('date'), errors='coerce').to_pydatetime()
                if pd.isna(date_val):
                    date_val = timezone.now()
            except Exception:
                date_val = timezone.now()

            # Use .get() for safe column access
            transactions_to_create.append(
                Transaction(
                    transaction_id=row.get('transaction_id', f"AUTO-{timezone.now().timestamp()}-{index}"),
                    amount=row.get('amount', 0),
                    date=date_val,
                    merchant=row.get('merchant', 'Unknown Merchant'),
                    card_number=str(row.get('card_number', 'N/A')),
                )
            )

        # 5. Bulk insert
        existing_ids = Transaction.objects.filter(
            transaction_id__in=[t.transaction_id for t in transactions_to_create]
        ).values_list('transaction_id', flat=True)

        new_transactions = [
            t for t in transactions_to_create if t.transaction_id not in existing_ids
        ]

        Transaction.objects.bulk_create(new_transactions, ignore_conflicts=True)

        new_rows_added = len(new_transactions)

        # 6. Log the action
        AuditLog.objects.create(
            action=f"File Upload Success: {file_name}",
            transaction_id=None,
            details=f"Successfully uploaded and processed {new_rows_added} new transaction records.",
            user="SYSTEM/User",
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return {"message": f"File processed. {new_rows_added} new records added!", "rows": new_rows_added}

    except Exception as e:
        error_message = f"Upload failed due to processing error: {str(e)}"

        # Attempt to log the failure (Best effort logging)
        try:
            AuditLog.objects.create(
                action=f"Upload Failed: {file_name}",
                details=error_message,
                user="SYSTEM/User",
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        except Exception:
            pass

        return {"error": error_message}