import tempfile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import User
from documents.models import Document
from documents.services.quota_service import QuotaService

class DocumentTests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@test.com", password="password", first_name="U1", last_name="T1", max_documents=2
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="password", first_name="U2", last_name="T2"
        )
        self.upload_url = reverse('document-list-create')
        
        self.dummy_pdf = SimpleUploadedFile(
            "test.pdf",
            b"%PDF-1.4 dummy content",
            content_type="application/pdf"
        )

    def test_upload_document_valid(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.upload_url, {"title": "Test Doc", "file": self.dummy_pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.status, Document.Status.UPLOADED)
        self.assertEqual(doc.uploaded_by, self.user1)

    def test_upload_document_quota_exceeded(self):
        self.client.force_authenticate(user=self.user1)
        # Upload 1st
        self.client.post(self.upload_url, {"title": "Doc1", "file": self.dummy_pdf}, format='multipart')
        # Upload 2nd
        self.dummy_pdf.seek(0)
        self.client.post(self.upload_url, {"title": "Doc2", "file": self.dummy_pdf}, format='multipart')
        
        # 3rd fails
        self.dummy_pdf.seek(0)
        response = self.client.post(self.upload_url, {"title": "Doc3", "file": self.dummy_pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Document.objects.count(), 2)

    def test_document_isolation_permissions(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.upload_url, {"title": "User1 Doc", "file": self.dummy_pdf}, format='multipart')
        doc = Document.objects.first()
        
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('document-detail', kwargs={'pk': doc.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
