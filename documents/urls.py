from django.urls import path

from .views import (
    DocumentListCreateView,
    DocumentDetailView,
    DocumentSummaryView,
    PresignedUrlView,
)


urlpatterns = [

    path(
        "",
        DocumentListCreateView.as_view(),
        name="document-list-create"
    ),

    path(
        "<int:pk>/",
        DocumentDetailView.as_view(),
        name="document-detail"
    ),

    path(
        "<int:pk>/summary/",
        DocumentSummaryView.as_view(),
        name="document-summary"
    ),

    path(
        "presigned-url/",
        PresignedUrlView.as_view(),
        name="presigned-url"
    ),

]