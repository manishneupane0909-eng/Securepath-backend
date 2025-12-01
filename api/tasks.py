# api/tasks.py
from celery import shared_task
import pandas as pd
import os
import io
import gzip
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.db.models import F, Q

# Import models
from api.models import Transaction, AuditLog


@shared_task
@transaction.atomic  # Ensures all database operations succeed or fail together
def process_uploaded_csv(file_path: str, file_name: str):
    """
    Background task to read, process, and bulk insert large CSV data.
    """
    try:
        start_time = timezone.now()

        # 1. Read file from disk
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # 2. Decompression (if needed)
        if file_name.endswith('.gz') or file_name.endswith('.gzip'):
            decompressed_data = gzip.decompress(file_data)
        else:
            decompressed_data = file_data

        # 3. Read into DataFrame (Memory intensive part)
        df = pd.read_csv(io.BytesIO(decompressed_data))
        initial_rows = len(df)

        # 4. Clean/Normalize DataFrame column names
        df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
        df.rename(columns={'txn_id': 'transaction_id', 'txn_date': 'date'}, inplace=True)

        # 5. Prepare data for bulk insert (Same logic as before)
        transactions_to_create = []
        for index, row in df.iterrows():
            try:
                date_val = pd.to_datetime(row.get('date'), errors='coerce').to_pydatetime()
                if pd.isna(date_val):
                    date_val = timezone.now()
            except Exception:
                date_val = timezone.now()

            transactions_to_create.append(
                Transaction(
                    transaction_id=row.get('transaction_id', f"AUTO-{timezone.now().timestamp()}-{index}"),
                    amount=row.get('amount', 0),
                    date=date_val,
                    merchant=row.get('merchant', 'Unknown Merchant'),
                    card_number=str(row.get('card_number', 'N/A')),
                )
            )

        # 6. Bulk insert (Only new records)
        existing_ids = Transaction.objects.filter(
            transaction_id__in=[t.transaction_id for t in transactions_to_create]
        ).values_list('transaction_id', flat=True)

        new_transactions = [
            t for t in transactions_to_create if t.transaction_id not in existing_ids
        ]

        Transaction.objects.bulk_create(new_transactions, ignore_conflicts=True)
        new_rows_added = len(new_transactions)

        # 7. Success Log
        AuditLog.objects.create(
            action=f"CSV Processed: {file_name}",
            details=f"Processed {initial_rows} rows. Added {new_rows_added} new records.",
            user="Celery Worker",
        )

        # 8. Clean up temporary file
        os.remove(file_path)

        return f"Completed: {new_rows_added} new records added."

    except Exception as e:
        # 9. Failure Log
        AuditLog.objects.create(
            action=f"CSV Processing Failed: {file_name}",
            details=f"Worker Error: {str(e)}",
            user="Celery Worker",
        )
        # Re-raise to mark task as failed in Celery
        raise e