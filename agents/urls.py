from django.urls import path
from .views import OrchestratorView

urlpatterns = [
    path("orchestrate/", OrchestratorView.as_view(), name="orchestrate"),
]
