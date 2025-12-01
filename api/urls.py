# api/urls.py
from django.urls import path
from ninja import NinjaAPI
from .router import router
from .auth import auth_bearer

api = NinjaAPI(csrf=False, auth=None)
api.add_router("", router)

urlpatterns = [path("", api.urls)]