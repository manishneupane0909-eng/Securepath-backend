# api/schemas.py
from ninja import Schema

class UploadResponse(Schema):
    status: str
    message: str
    records_uploaded: int
    duplicates_removed: int
    duration_seconds: float

class TransactionOut(Schema):
    id: int
    transaction_id: str
    amount: float = None
    merchant: str = None
    date: str = None
    risk_score: float = None
    reason_code: str = None
    status: str
    risk_level: str

class DashboardStats(Schema):
    total_transactions: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    pending_count: int
    approved_count: int
    rejected_count: int
    avg_risk_score: float
    total_amount: float

class DecisionIn(Schema):
    transaction_id: str
    decision: str
    reason: str = ""

class FraudDetectionResult(Schema):
    total_processed: int
    flagged_count: int
    duration_seconds: float
    results: list