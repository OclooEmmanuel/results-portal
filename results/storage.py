from django.conf import settings
from django.core.files.storage import Storage
from supabase import create_client
import uuid


class SupabaseStorage(Storage):

    def __init__(self):
        self.client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket = settings.SUPABASE_BUCKET

    def _save(self, name, content):
        file_name = f"{uuid.uuid4()}_{name}"

        file_bytes = content.read()

        self.client.storage.from_(self.bucket).upload(
            file_name,
            file_bytes
        )

        return file_name

    def url(self, name):
        return self.client.storage.from_(self.bucket).get_public_url(name)
