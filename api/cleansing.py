# api/cleansing.py
import pandas as pd


def cleanse_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    ATC-02: Data Cleansing
    - Remove duplicates by transaction_id
    - Normalize timestamps to YYYY-MM-DD HH:MM:SS
    - Normalize currency amounts to 2 decimals
    - Normalize country and currency codes
    """
    # Remove duplicates
    df = df.drop_duplicates(subset=['transaction_id'], keep='first')

    # Normalize timestamps
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Normalize currency amounts
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['amount'] = df['amount'].round(2)

    # Normalize country codes
    if 'country' in df.columns:
        df['country'] = df['country'].str.upper().str.strip()

    # Normalize currency codes
    if 'currency' in df.columns:
        df['currency'] = df['currency'].str.upper().str.strip()

    return df