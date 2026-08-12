from django.contrib import admin
from django.urls import path, include
from core.health import HealthCheckView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    # ── Health Check ──────────────────────────────────
    path(
        "api/health/",
        HealthCheckView.as_view(),
        name="health-check"
    ),

    # ── Auth & Users ──────────────────────────────────
    path(
        "api/auth/",
        include("users.urls")
    ),

    # ── Documents ─────────────────────────────────────
    path(
        "api/documents/",
        include("documents.urls")
    ),

    # ── Chat ──────────────────────────────────────────
    path(
        "api/chat/",
        include("chat.urls")
    ),

    # ── Quiz ──────────────────────────────────────────
    path(
        "api/quiz/",
        include("quiz.urls")
    ),

    # ── Agents ────────────────────────────────────────
    path(
        "api/agents/",
        include("agents.urls")
    ),

    # ── Analytics ─────────────────────────────────────
    path(
        "api/analytics/",
        include("analytics.urls")
    ),

    # ── Notifications ─────────────────────────────────
    path(
        "api/notifications/",
        include("notifications.urls")
    ),

    # ── API Documentation (Swagger / OpenAPI) ─────────
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema"
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui"
    ),

    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc"
    ),

]