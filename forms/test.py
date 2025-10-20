# forms/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from forms.models import Form, FormView, Category
import uuid

User = get_user_model()

class FormAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='StrongPass123!', full_name='User One')
        self.other = User.objects.create_user(email='o@example.com', password='StrongPass123!', full_name='Other User')
        self.client.login(email='u@example.com', password='StrongPass123!')  # اگر JWT دارید، به‌جای login از token استفاده کنید

    def test_create_form_public(self):
        url = reverse('forms:form-list')
        data = {'title': 'Form A', 'description': 'Desc', 'is_public': True}
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.filter(created_by=self.user).count(), 1)

    def test_list_forms_only_own(self):
        Form.objects.create(title='X', description='', created_by=self.user)
        Form.objects.create(title='Y', description='', created_by=self.other)
        url = reverse('forms:form-list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_public_view_logs_view(self):
        f = Form.objects.create(title='Pub', description='', is_public=True, created_by=self.user)
        url = reverse('forms:form-public', args=[str(f.id)])
        res = self.client.get(url)  # اجازه عمومی
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(FormView.objects.filter(form=f).count(), 1)

    def test_stats_requires_owner(self):
        f = Form.objects.create(title='A', description='', is_public=True, created_by=self.other)
        url = reverse('forms:form-stats', args=[str(f.id)])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

class CategoryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='StrongPass123!', full_name='User One')
        self.client.login(email='u@example.com', password='StrongPass123!')

    def test_category_crud(self):
        list_url = reverse('forms:category-list')
        create_res = self.client.post(list_url, {'name': 'Group 1', 'description': '...'}, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        cat_id = create_res.data['id']
        detail_url = reverse('forms:category-detail', args=[cat_id])

        get_res = self.client.get(detail_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)

        patch_res = self.client.patch(detail_url, {'name': 'Group 2'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)