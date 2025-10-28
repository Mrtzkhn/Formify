from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from forms.models import Category, EntityCategory, Form, Process

User = get_user_model()


class CategoryAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            full_name='Other User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # API URLs
        self.list_url = '/api/v1/forms/categories/'
        self.create_url = '/api/v1/forms/categories/'

    def test_create_category_success(self):
        """Test successful category creation."""
        data = {
            'name': 'Test Category',
            'description': 'Test Category Description'
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        
        category = Category.objects.first()
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.created_by, self.user)

    def test_create_category_duplicate_name(self):
        """Test category creation with duplicate name."""
        # Create first category
        Category.objects.create(
            name='Duplicate Category',
            description='First Category',
            created_by=self.user
        )
        
        data = {
            'name': 'Duplicate Category',
            'description': 'Second Category'
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_list_categories(self):
        """Test listing user's categories."""
        # Create categories for both users
        Category.objects.create(
            name='User Category 1',
            description='Description 1',
            created_by=self.user
        )
        Category.objects.create(
            name='User Category 2',
            description='Description 2',
            created_by=self.user
        )
        Category.objects.create(
            name='Other User Category',
            description='Other Description',
            created_by=self.other_user
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only user's categories
        self.assertEqual(response.data[0]['name'], 'User Category 1')
        self.assertEqual(response.data[1]['name'], 'User Category 2')

    def test_retrieve_category_success(self):
        """Test successful category retrieval."""
        category = Category.objects.create(
            name='Retrieve Category',
            description='Retrieve Description',
            created_by=self.user
        )
        
        url = f'/api/v1/forms/categories/{category.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Category')

    def test_retrieve_category_other_user(self):
        """Test retrieving another user's category."""
        category = Category.objects.create(
            name='Other User Category',
            description='Other Description',
            created_by=self.other_user
        )
        
        url = f'/api/v1/forms/categories/{category.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_category_success(self):
        """Test successful category update."""
        category = Category.objects.create(
            name='Original Category',
            description='Original Description',
            created_by=self.user
        )
        
        data = {
            'name': 'Updated Category',
            'description': 'Updated Description'
        }
        
        url = f'/api/v1/forms/categories/{category.id}/'
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category.refresh_from_db()
        self.assertEqual(category.name, 'Updated Category')
        self.assertEqual(category.description, 'Updated Description')

    def test_delete_category_success(self):
        """Test successful category deletion."""
        category = Category.objects.create(
            name='Delete Category',
            description='Delete Description',
            created_by=self.user
        )
        
        url = f'/api/v1/forms/categories/{category.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_delete_category_with_entities(self):
        """Test deleting category with entity associations."""
        category = Category.objects.create(
            name='Category with Entities',
            description='Description',
            created_by=self.user
        )
        
        form = Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        
        EntityCategory.objects.create(
            entity_type='form',
            entity_id=form.id,
            category=category
        )
        
        url = f'/api/v1/forms/categories/{category.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access endpoints."""
        self.client.logout()
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post(self.create_url, {'name': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EntityCategoryAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            full_name='Other User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            created_by=self.user
        )
        
        self.form = Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        
        self.process = Process.objects.create(
            title='Test Process',
            description='Test Description',
            process_type='linear',
            created_by=self.user
        )
        
        # API URLs
        self.list_url = '/api/v1/forms/entity-categories/'
        self.create_url = '/api/v1/forms/entity-categories/'
        self.by_entity_url = '/api/v1/forms/entity-categories/by_entity/'

    def test_create_entity_category_form_success(self):
        """Test successful entity category creation for form."""
        data = {
            'entity_type': 'form',
            'entity_id': self.form.id,
            'category': self.category.id
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EntityCategory.objects.count(), 1)
        
        entity_category = EntityCategory.objects.first()
        self.assertEqual(entity_category.entity_type, 'form')
        self.assertEqual(entity_category.entity_id, self.form.id)
        self.assertEqual(entity_category.category, self.category)

    def test_create_entity_category_process_success(self):
        """Test successful entity category creation for process."""
        data = {
            'entity_type': 'process',
            'entity_id': self.process.id,
            'category': self.category.id
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EntityCategory.objects.count(), 1)
        
        entity_category = EntityCategory.objects.first()
        self.assertEqual(entity_category.entity_type, 'process')
        self.assertEqual(entity_category.entity_id, self.process.id)
        self.assertEqual(entity_category.category, self.category)

    def test_create_entity_category_other_user_category(self):
        """Test creating entity category with category from another user."""
        other_category = Category.objects.create(
            name='Other Category',
            description='Other Description',
            created_by=self.other_user
        )
        
        data = {
            'entity_type': 'form',
            'entity_id': self.form.id,
            'category': other_category.id
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_list_entity_categories(self):
        """Test listing user's entity categories."""
        # Create entity categories
        EntityCategory.objects.create(
            entity_type='form',
            entity_id=self.form.id,
            category=self.category
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['entity_type'], 'form')

    def test_by_entity_action(self):
        """Test the by_entity custom action."""
        EntityCategory.objects.create(
            entity_type='form',
            entity_id=self.form.id,
            category=self.category
        )
        
        url = f'{self.by_entity_url}?entity_type=form&entity_id={self.form.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['entity_type'], 'form')

    def test_by_entity_action_missing_params(self):
        """Test by_entity action without required parameters."""
        url = self.by_entity_url
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_delete_entity_category_success(self):
        """Test successful entity category deletion."""
        entity_category = EntityCategory.objects.create(
            entity_type='form',
            entity_id=self.form.id,
            category=self.category
        )
        
        url = f'/api/v1/forms/entity-categories/{entity_category.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(EntityCategory.objects.count(), 0)
