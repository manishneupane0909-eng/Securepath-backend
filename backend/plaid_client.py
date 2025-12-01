# backend/plaid_client.py ← REPLACE ENTIRE FILE WITH THIS
import os
import json
from datetime import datetime, timedelta
from plaid import Configuration, ApiClient
from plaid.api import plaid_api

# Correct modern way (2024–2025)
configuration = Configuration(
    host="https://sandbox.plaid.com" if os.getenv("PLAID_ENV",
                                                  "sandbox") == "sandbox" else "https://development.plaid.com",
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
    }
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


def create_link_token():
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser

    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="securepath-2025"),
        client_name="SecurePath FRDS",
        products=["transactions"],
        country_codes=["US"],
        language="en"
    )
    response = client.link_token_create(request)
    return response.link_token


def exchange_public_token(public_token: str):
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
    request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(request)
    return response.access_token


def fetch_transactions(access_token: str = None):
    cache_path = "/app/data/cached_transactions.json"
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    try:
        if not access_token:
            raise Exception("No access token")

        from plaid.model.transactions_get_request import TransactionsGetRequest
        from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=(datetime.now() - timedelta(days=730)).date(),
            end_date=datetime.now().date()
        )
        response = client.transactions_get(request)
        transactions = [t.to_dict() for t in response.transactions]

        with open(cache_path, "w") as f:
            json.dump(transactions, f, indent=2, default=str)

        return {"transactions": transactions, "source": "plaid"}

    except Exception as e:
        print(f"Plaid failed: {e}")
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                cached = json.load(f)
            return {"transactions": cached, "source": "cache"}
        return {"transactions": [], "source": "none"}