from django.urls import path
from core.views.dashboard_view import dashboard_view

app_name = "core"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
]