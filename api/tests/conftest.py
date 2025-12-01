# api/tests/conftest.py - Pytest configuration and fixtures
import pytest
from django.utils import timezone
from decimal import Decimal
from api.models import Transaction, AuditLog


@pytest.fixture
def sample_transaction():
    """Fixture to create a sample transaction"""
    return Transaction.objects.create(
        transaction_id="FIXTURE-001",
        amount=Decimal("250.00"),
        date=timezone.now(),
        merchant="Test Merchant",
        card_number="1234567890123456",
        status="pending"
    )


@pytest.fixture
def fraud_transaction():
    """Fixture to create a fraudulent transaction"""
    return Transaction.objects.create(
        transaction_id="FRAUD-001",
        amount=Decimal("7500.00"),
        date=timezone.now(),
        merchant="Suspicious Merchant",
        card_number="9999888877776666",
        is_fraud=True,
        fraud_score=Decimal("0.95"),
        risk_score=Decimal("95.0"),
        fraud_reasons="High amount + suspicious merchant",
        status="rejected"
    )


@pytest.fixture
def multiple_transactions():
    """Fixture to create multiple transactions"""
    transactions = []
    for i in range(5):
        txn = Transaction.objects.create(
            transaction_id=f"BULK-{i:03d}",
            amount=Decimal(f"{100 + i * 50}.00"),
            date=timezone.now(),
            merchant=f"Merchant {i}",
            card_number=f"1234567890{i:06d}",
            status="pending"
        )
        transactions.append(txn)
    return transactions


@pytest.fixture
def api_token():
    """Fixture to provide API authentication token"""
    return "root"
