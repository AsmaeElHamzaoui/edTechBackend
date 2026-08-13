from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


class HealthCheckView(APIView):
    """
    GET /api/health/
    Vérifie la connectivité des services principaux.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        health = {
            "status": "healthy",
            "services": {}
        }

        # ── Database ──────────────────────────────────
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health["services"]["database"] = "ok"
        except Exception as e:
            health["services"]["database"] = f"error: {e}"
            health["status"] = "degraded"

        # ── Redis / Celery broker ─────────────────────
        try:
            from django.conf import settings
            import redis as redis_lib
            r = redis_lib.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            health["services"]["redis"] = "ok"
        except Exception:
            health["services"]["redis"] = "unavailable"

        # ── ChromaDB (vector store) ───────────────────
        try:
            from documents.services.embedding_service import collection
            collection.count()
            health["services"]["vector_db"] = "ok"
        except Exception:
            health["services"]["vector_db"] = "unavailable"

        http_status = status.HTTP_200_OK if health["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(health, status=http_status)
