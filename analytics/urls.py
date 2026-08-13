from django.urls import path
from .views import (
    DashboardView,
    LearningSessionCreateView,
    ProgressView,
    ConceptsView,
    RecommendationsView,
    ExportCSVView,
    ExportPDFView,
)

urlpatterns = [
    path("dashboard/",          DashboardView.as_view(),           name="analytics-dashboard"),
    path("progress/",           ProgressView.as_view(),            name="analytics-progress"),
    path("concepts/",           ConceptsView.as_view(),            name="analytics-concepts"),
    path("recommendations/",    RecommendationsView.as_view(),     name="analytics-recommendations"),
    path("export/csv/",         ExportCSVView.as_view(),           name="analytics-export-csv"),
    path("export/pdf/",         ExportPDFView.as_view(),           name="analytics-export-pdf"),
    path("sessions/",           LearningSessionCreateView.as_view(), name="analytics-session-create"),
]
