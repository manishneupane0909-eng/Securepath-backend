# api/models.py - COMPLETE VERSION
"""
LOCATION: securepath-backend/api/models.py
Replace your entire models.py with this
"""

from django.db import models
from django.utils import timezone


class Transaction(models.Model):
    """Main transaction model with all required fields"""

    # Core transaction fields
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(db_index=True)
    merchant = models.CharField(max_length=200)
    card_number = models.CharField(max_length=20)

    # Additional context fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=2, default='US')
    currency = models.CharField(max_length=3, default='USD')

    # Fraud detection fields
    fraud_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Rule-based risk score (0-100)")
    is_fraud = models.BooleanField(default=False, db_index=True)
    fraud_reasons = models.TextField(null=True, blank=True)
    reason_code = models.TextField(null=True, blank=True, help_text="Detailed fraud detection reasons")

    # Status tracking
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['is_fraud']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - ${self.amount} - {self.status}"


class AuditLog(models.Model):
    """Audit log for tracking all system actions"""

    # Action details
    action = models.CharField(max_length=100, db_index=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    details = models.TextField(null=True, blank=True)

    # User context
    user = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class SystemMetrics(models.Model):
    """System performance and health metrics"""

    # Performance metrics
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    memory_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Transaction metrics
    active_transactions = models.IntegerField(default=0)
    total_transactions = models.IntegerField(default=0)
    fraud_detected = models.IntegerField(default=0)

    # Response time metrics
    avg_response_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "System Metrics"

    def __str__(self):
        return f"Metrics - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"