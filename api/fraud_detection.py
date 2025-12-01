# api/fraud_detection.py
import numpy as np
import joblib
import os
from .models import Transaction


def load_ml_model():
    """Load ML model if exists, otherwise return None"""
    model_path = "fraud_model.pkl"
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except Exception as e:
            print(f"Model load failed: {e}")
            return None
    return None


def calculate_rule_score(txn):
    """ATC-03: Rule-based fraud detection"""
    reasons = []
    score = 0

    # Rule 1: High amount (>$5,000)
    if txn.amount and txn.amount > 5000:
        reasons.append("R1: High Amount (>$5,000)")
        score += 30

    # Rule 2: Foreign country
    if txn.country and txn.country != "US":
        reasons.append("R2: Foreign Country")
        score += 25

    # Rule 3: High velocity IP
    if txn.ip_address:
        ip_count = Transaction.objects.filter(ip_address=txn.ip_address).count()
        if ip_count > 10:
            reasons.append("R3: High Velocity IP")
            score += 20

    # Rule 4: New device
    if "new" in str(txn.device_id).lower():
        reasons.append("R4: New Device")
        score += 15

    # Rule 5: New IP Address (ATC-03)
    if txn.ip_address:
        # Check if this IP has been seen before (excluding current transaction)
        ip_exists = Transaction.objects.filter(ip_address=txn.ip_address).exclude(id=txn.id).exists()
        if not ip_exists:
            reasons.append("R5: New IP Address")
            score += 10

    return score, reasons


def prepare_ml_features(transactions):
    """Prepare feature matrix for ML model"""
    features = []
    for t in transactions:
        feature = [
            float(t.amount or 0),
            1 if t.amount and t.amount > 5000 else 0,
            1 if t.country and t.country != "US" else 0,
            1 if "new" in str(t.device_id).lower() else 0,
            Transaction.objects.filter(ip_address=t.ip_address).count() if t.ip_address else 1
        ]
        features.append(feature)
    return np.array(features)


def calculate_ml_scores(model, features):
    """ATC-04: ML-based scoring"""
    try:
        ml_scores = model.decision_function(features) * -1
        ml_scores = (ml_scores - ml_scores.min()) / (ml_scores.max() - ml_scores.min() + 1e-10) * 100
        return ml_scores
    except:
        return np.zeros(len(features))


def detect_fraud(transactions):
    """
    Main fraud detection function
    Combines rule-based (ATC-03) and ML-based (ATC-04) detection
    """
    model = load_ml_model()
    use_ml = model is not None

    # Prepare ML features
    if use_ml:
        features = prepare_ml_features(transactions)
        ml_scores = calculate_ml_scores(model, features)
    else:
        ml_scores = np.zeros(len(transactions))

    results = []
    flagged_count = 0

    for i, txn in enumerate(transactions):
        # Calculate rule-based score
        rule_score, reasons = calculate_rule_score(txn)

        # Get ML score
        ml_score = ml_scores[i] if use_ml else 0

        # Combine scores (60% rules, 40% ML)
        final_score = min(100, (rule_score * 0.6 + ml_score * 0.4))

        # Add ML reason if high score
        if use_ml and ml_score > 70:
            reasons.append("ML: Anomaly Detected")

        reason_text = " | ".join(reasons) if reasons else "No risk flags detected"

        # Save to database
        txn.risk_score = round(final_score, 1)
        txn.reason_code = reason_text
        txn.save()

        is_flagged = final_score >= 70
        if is_flagged:
            flagged_count += 1

        results.append({
            "id": txn.id,
            "transaction_id": txn.transaction_id,
            "risk_score": round(final_score, 1),
            "reason_code": reason_text,
            "flagged": is_flagged
        })

    return results, flagged_count