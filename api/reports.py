# api/reports.py
import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from .models import Transaction


def generate_csv_report(transactions):
    """ATC-07: Generate CSV report"""
    output = io.StringIO()

    df = pd.DataFrame([
        {
            "Transaction ID": t.transaction_id,
            "Date": t.date.strftime('%Y-%m-%d %H:%M:%S') if t.date else "",
            "Merchant": t.merchant,
            "Amount": float(t.amount) if t.amount else 0,
            "Risk Score": t.risk_score or 0,
            "Risk Level": t.risk_level,
            "Status": t.status,
            "Reason Code": t.reason_code,
            "Country": t.country,
            "Currency": t.currency
        }
        for t in transactions
    ])

    df.to_csv(output, index=False)
    output.seek(0)

    return output.getvalue()


def generate_pdf_report(transactions, stats):
    """ATC-07: Generate PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("Fraud & Risk Detection Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Summary statistics
    summary_text = f"""
    <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    <b>Total Transactions:</b> {stats['total_transactions']}<br/>
    <b>High Risk:</b> {stats['high_risk_count']} | 
    <b>Medium Risk:</b> {stats['medium_risk_count']} | 
    <b>Low Risk:</b> {stats['low_risk_count']}<br/>
    <b>Pending:</b> {stats['pending_count']} | 
    <b>Approved:</b> {stats['approved_count']} | 
    <b>Rejected:</b> {stats['rejected_count']}<br/>
    <b>Average Risk Score:</b> {stats['avg_risk_score']:.1f}<br/>
    <b>Total Amount:</b> ${stats['total_amount']:.2f}
    """
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Transaction table (limited to 50 for PDF)
    table_data = [['ID', 'Merchant', 'Amount', 'Risk', 'Status']]
    for t in transactions[:50]:
        table_data.append([
            t.transaction_id[:10],
            (t.merchant or "")[:20],
            f"${t.amount:.2f}" if t.amount else "$0.00",
            f"{t.risk_score:.1f}" if t.risk_score else "N/A",
            t.status
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()