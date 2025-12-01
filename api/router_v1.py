# api/router_v1.py - Versioned API router with rate limiting
from ninja import Router, File, UploadedFile
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import cache_page
from api.auth import auth_bearer, token_query_auth
import pandas as pd
import io
import csv
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
import logging

from api.models import Transaction, SystemMetrics, AuditLog

logger = logging.getLogger('api')
router = Router()


@router.get("/status", auth=None)
def status(request):
    """Health check endpoint - no authentication required"""
    return {
        "status": "ok",
        "message": "SecurePath API v1 is running",
        "version": "1.0.0",
        "timestamp": timezone.now().isoformat()
    }


@router.get("/dashboard/stats", auth=auth_bearer)
def stats(request):
    """Returns high-level statistics with caching"""
    try:
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
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return {"error": "Failed to fetch statistics"}, 500


@router.get("/dashboard/transactions", auth=auth_bearer)
@ratelimit(key='user', rate='100/m', method='GET')
def transactions(request, page: int = 1, page_size: int = 10, status_filter: str = None):
    """Returns paginated transactions with optional filtering"""
    try:
        # Validate pagination parameters
        page = max(1, page)
        page_size = min(max(1, page_size), 100)  # Max 100 items per page
        
        offset = (page - 1) * page_size
        limit = page_size

        # Build query
        query = Transaction.objects.all()
        
        # Apply filters
        if status_filter and status_filter in ['pending', 'approved', 'rejected']:
            query = query.filter(status=status_filter)

        # Get total count for pagination
        total_count = query.count()
        
        # Get paginated results
        txns = query.order_by('-date')[offset:offset + limit]

        txn_list = [{
            "transaction_id": txn.transaction_id,
            "amount": float(txn.amount),
            "merchant": txn.merchant,
            "status": txn.status,
            "fraud_score": float(txn.fraud_score or 0.0),
            "risk_score": float(txn.risk_score or 0.0),
            "is_fraud": txn.is_fraud,
            "date": txn.date.isoformat() if txn.date else None,
        } for txn in txns]

        return {
            "transactions": txn_list,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        return {"error": "Failed to fetch transactions"}, 500


@router.get("/audit-log", auth=auth_bearer)
@ratelimit(key='user', rate='50/m', method='GET')
def audit_log(request, page: int = 1, page_size: int = 20):
    """Returns paginated audit logs"""
    try:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        
        offset = (page - 1) * page_size
        limit = page_size

        total_count = AuditLog.objects.count()
        logs = AuditLog.objects.all().order_by('-timestamp')[offset:offset + limit]

        log_list = [{
            "action": log.action,
            "transaction_id": log.transaction_id,
            "details": log.details,
            "user": log.user,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        } for log in logs]

        return {
            "logs": log_list,
            "total": total_count,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(f"Error fetching audit logs: {str(e)}")
        return {"error": "Failed to fetch audit logs"}, 500


@router.post("/detect-fraud", auth=auth_bearer)
@ratelimit(key='user', rate='10/m', method='POST')
def detect_fraud(request):
    """
    Optimized fraud detection with rate limiting
    """
    try:
        start_time = timezone.now()
        HIGH_RISK_AMOUNT = Decimal('5000.00')
        HIGH_SCORE = Decimal('0.5')

        transactions_to_process = Transaction.objects.filter(
            Q(status='pending') | Q(status='review')
        )
        processed_count = transactions_to_process.count()

        # Bulk update high-risk transactions
        high_risk_txns = transactions_to_process.filter(amount__gte=HIGH_RISK_AMOUNT)
        fraud_count = high_risk_txns.count()

        high_risk_txns.update(
            is_fraud=True,
            fraud_score=HIGH_SCORE,
            risk_score=Decimal('80.0'),
            fraud_reasons='High transaction amount (>= $5000).',
            reason_code='R1: High Amount',
            status='rejected'
        )

        # Approve remaining transactions
        transactions_to_approve = transactions_to_process.exclude(is_fraud=True)
        transactions_to_approve.update(
            is_fraud=False,
            fraud_score=Decimal('0.0'),
            risk_score=Decimal('10.0'),
            fraud_reasons='',
            reason_code='',
            status='approved'
        )

        # Log the action
        AuditLog.objects.create(
            action="Fraud Detection Run (Bulk Optimized)",
            details=f"Processed {processed_count} transactions. Detected {fraud_count} fraud attempts.",
            user="SYSTEM",
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        duration = (timezone.now() - start_time).total_seconds()

        return {
            "status": "success",
            "message": f"Detection complete. {processed_count} processed in {round(duration, 3)}s.",
            "transactions_processed": processed_count,
            "fraud_detected": fraud_count,
            "duration_seconds": round(duration, 3)
        }
    except Exception as e:
        logger.error(f"Error in fraud detection: {str(e)}")
        return {"error": "Fraud detection failed", "message": str(e)}, 500





@router.post("/upload", auth=auth_bearer)
@ratelimit(key='user', rate='10/h', method='POST')
def upload_file(request, file: UploadedFile = File(...)):
    """
    Handles file upload with rate limiting
    """
    try:
        file_name = file.name
        file_data = file.read()

        df = pd.read_csv(io.BytesIO(file_data))
        initial_rows = len(df)

        # Clean column names
        df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
        df.rename(columns={'txn_id': 'transaction_id', 'txn_date': 'date'}, inplace=True)

        # Prepare bulk insert
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

        # Bulk insert
        existing_ids = Transaction.objects.filter(
            transaction_id__in=[t.transaction_id for t in transactions_to_create]
        ).values_list('transaction_id', flat=True)

        new_transactions = [
            t for t in transactions_to_create if t.transaction_id not in existing_ids
        ]

        Transaction.objects.bulk_create(new_transactions, ignore_conflicts=True)
        new_rows_added = len(new_transactions)

        # Log success
        AuditLog.objects.create(
            action=f"File Upload Success: {file_name}",
            details=f"Successfully uploaded {new_rows_added} new transaction records.",
            user="SYSTEM/User",
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return {
            "message": f"File processed. {new_rows_added} new records added!",
            "rows": new_rows_added,
            "total_rows": initial_rows
        }

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        
        # Log failure
        try:
            AuditLog.objects.create(
                action=f"Upload Failed: {file_name}",
                details=str(e),
                user="SYSTEM/User",
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        except Exception:
            pass

        return {"error": f"Upload failed: {str(e)}"}, 500


# ==========================================
# PLAID INTEGRATION
# ==========================================
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from django.conf import settings
import datetime

def get_plaid_client():
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox if settings.PLAID_ENV == 'sandbox' else plaid.Environment.Development,
        api_key={
            'clientId': settings.PLAID_CLIENT_ID,
            'secret': settings.PLAID_SECRET,
        }
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)

@router.post("/plaid/create_link_token", auth=auth_bearer)
def create_link_token(request):
    try:
        client = get_plaid_client()
        request_data = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name="SecurePath Fraud Detection",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id=str(request.user.id if request.user.is_authenticated else 'guest_user')
            )
        )
        response = client.link_token_create(request_data)
        return {"link_token": response['link_token']}
    except Exception as e:
        logger.error(f"Plaid Link Token Error: {str(e)}")
        return {"error": str(e)}, 500

@router.post("/plaid/exchange_public_token", auth=auth_bearer)
def exchange_public_token(request, public_token: str):
    try:
        client = get_plaid_client()
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = client.item_public_token_exchange(exchange_request)
        return {"access_token": response['access_token']}
    except Exception as e:
        logger.error(f"Plaid Exchange Error: {str(e)}")
        return {"error": str(e)}, 500

@router.get("/plaid/transactions", auth=auth_bearer)
def get_plaid_transactions(request, access_token: str):
    try:
        client = get_plaid_client()
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).date()
        end_date = datetime.datetime.now().date()
        
        request_data = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )
        response = client.transactions_get(request_data)
        transactions = response['transactions']
        
        # Convert to our format and save
        saved_count = 0
        txns_to_create = []
        
        for t in transactions:
            txns_to_create.append(Transaction(
                transaction_id=t['transaction_id'],
                amount=Decimal(str(t['amount'])),
                date=t['date'],
                merchant=t['name'],
                status='pending'
            ))
            
        Transaction.objects.bulk_create(txns_to_create, ignore_conflicts=True)
        saved_count = len(txns_to_create)
        
        return {
            "message": "Transactions synced",
            "count": saved_count,
            "transactions": [t.to_dict() for t in transactions]
        }
    except Exception as e:
        logger.error(f"Plaid Transactions Error: {str(e)}")
        return {"error": str(e)}, 500
