from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    RegisterView,
    ProfileView,
    AdminUserListView,
    AdminUserDetailView,
    AuditLogListView,
)


urlpatterns = [

    # ── Authentification ──────────────────────────────────
    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "login/",
        TokenObtainPairView.as_view(),
        name="login"
    ),

    path(
        "refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),

    path(
        "profile/",
        ProfileView.as_view(),
        name="profile"
    ),

    # ── Administration (ADMIN uniquement) ─────────────────
    path(
        "admin/users/",
        AdminUserListView.as_view(),
        name="admin-user-list"
    ),

    path(
        "admin/users/<int:pk>/",
        AdminUserDetailView.as_view(),
        name="admin-user-detail"
    ),

    path(
        "admin/audit-log/",
        AuditLogListView.as_view(),
        name="admin-audit-log"
    ),
]