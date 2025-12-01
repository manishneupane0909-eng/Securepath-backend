# backend/urls.py - Updated with API versioning
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from api.router_v1 import router as router_v1

# Create versioned API instance
api_v1 = NinjaAPI(version='1.0.0', title='SecurePath API', description='Fraud Detection System API')
api_v1.add_router("/", router_v1)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_v1.urls),  # Main API endpoint (supports both /api/ and /api/v1/ via router)
]