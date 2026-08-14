from django.conf import settings

class QuotaService:

    @staticmethod
    def can_upload(user, file_size: int) -> tuple[bool, str]:
        if user.documents.count() >= user.max_documents:
            return False, f"Vous avez atteint la limite de {user.max_documents} documents."
            
        if user.used_storage_bytes + file_size > user.max_storage_bytes:
            remaining = max(0, user.max_storage_bytes - user.used_storage_bytes)
            return False, f"Espace insuffisant. Il vous reste {remaining / 1_000_000:.2f} MB."
            
        return True, ""

    @staticmethod
    def reserve_storage(user, file_size: int):
        user.used_storage_bytes += file_size
        user.save(update_fields=["used_storage_bytes"])

    @staticmethod
    def release_storage(user, file_size: int):
        user.used_storage_bytes = max(0, user.used_storage_bytes - file_size)
        user.save(update_fields=["used_storage_bytes"])
