from django.contrib import admin   # 👈 this import is required
from django.urls import path, include
from django.http import JsonResponse

def root_view(request):
    return JsonResponse({"message": "Welcome to SecurePath API. Use /api/ for endpoints."})

urlpatterns = [
    path('', root_view),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
