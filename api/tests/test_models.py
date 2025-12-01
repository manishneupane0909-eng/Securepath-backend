# api/tests/test_models.py
import pytest
from django.utils import timezone
from decimal import Decimal
from api.models import Transaction, AuditLog, SystemMetrics


@pytest.mark.django_db
class TestTransactionModel:
    """Test cases for Transaction model"""
    
    def test_create_transaction(self):
        """Test creating a basic transaction"""
        txn = Transaction.objects.create(
            transaction_id="TEST-001",
            amount=Decimal("100.50"),
            date=timezone.now(),
            merchant="Test Merchant",
            card_number="1234567890123456"
        )
        
        assert txn.transaction_id == "TEST-001"
        assert txn.amount == Decimal("100.50")
        assert txn.status == "pending"
        assert txn.is_fraud is False
    
    def test_transaction_fraud_detection(self):
        """Test fraud detection fields"""
        txn = Transaction.objects.create(
            transaction_id="TEST-002",
            amount=Decimal("6000.00"),
            date=timezone.now(),
            merchant="Suspicious Merchant",
            card_number="9876543210987654",
            is_fraud=True,
            fraud_score=Decimal("0.85"),
            risk_score=Decimal("90.0"),
            fraud_reasons="High amount transaction"
        )
        
        assert txn.is_fraud is True
        assert txn.fraud_score == Decimal("0.85")
        assert txn.risk_score == Decimal("90.0")
    
    def test_transaction_status_choices(self):
        """Test transaction status updates"""
        txn = Transaction.objects.create(
            transaction_id="TEST-003",
            amount=Decimal("50.00"),
            date=timezone.now(),
            merchant="Normal Merchant",
            card_number="1111222233334444"
        )
        
        assert txn.status == "pending"
        
        txn.status = "approved"
        txn.save()
        
        assert txn.status == "approved"


@pytest.mark.django_db
class TestAuditLogModel:
    """Test cases for AuditLog model"""
    
    def test_create_audit_log(self):
        """Test creating an audit log entry"""
        log = AuditLog.objects.create(
            action="Test Action",
            transaction_id="TEST-001",
            details="Test details",
            user="test_user",
            ip_address="127.0.0.1"
        )
        
        assert log.action == "Test Action"
        assert log.transaction_id == "TEST-001"
        assert log.user == "test_user"


@pytest.mark.django_db
class TestSystemMetricsModel:
    """Test cases for SystemMetrics model"""
    
    def test_create_system_metrics(self):
        """Test creating system metrics"""
        metrics = SystemMetrics.objects.create(
            cpu_usage=Decimal("45.5"),
            memory_usage=Decimal("60.2"),
            active_transactions=100,
            total_transactions=1000,
            fraud_detected=10
        )
        
        assert metrics.cpu_usage == Decimal("45.5")
        assert metrics.total_transactions == 1000
        assert metrics.fraud_detected == 10
