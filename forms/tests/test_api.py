from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from forms.models import Form, Field

User = get_user_model()


class FieldAPITestCase(APITestCase):
    """Test cases for Field API endpoints."""
    
    def setUp(self):
        """Set up test data."""
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
        
        self.form = Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        self.other_form = Form.objects.create(
            title='Other Form',
            description='Other Description',
            created_by=self.other_user
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_field_success(self):
        """Test successful field creation via API."""
        url = '/api/v1/forms/fields/'
        data = {
            'form': str(self.form.id),
            'label': 'Test Field',
            'field_type': 'text',
            'is_required': True,
            'options': {},
            'order_num': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Field.objects.count(), 1)
        
        field = Field.objects.first()
        self.assertEqual(field.label, 'Test Field')
        self.assertEqual(field.field_type, 'text')
        self.assertTrue(field.is_required)
    
    def test_create_field_permission_denied(self):
        """Test field creation with permission denied."""
        url = '/api/v1/forms/fields/'
        data = {
            'form': str(self.other_form.id),  # Form owned by other user
            'label': 'Test Field',
            'field_type': 'text',
            'is_required': True,
            'options': {},
            'order_num': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Field.objects.count(), 0)
    
    def test_create_select_field_with_options(self):
        """Test creating a select field with valid options."""
        url = '/api/v1/forms/fields/'
        data = {
            'form': str(self.form.id),
            'label': 'Country',
            'field_type': 'select',
            'is_required': True,
            'options': {
                'choices': [
                    {'value': 'us', 'label': 'United States'},
                    {'value': 'ca', 'label': 'Canada'}
                ]
            },
            'order_num': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        field = Field.objects.first()
        self.assertEqual(field.field_type, 'select')
        self.assertIn('choices', field.options)
    
    def test_create_field_invalid_options(self):
        """Test field creation with invalid options."""
        url = '/api/v1/forms/fields/'
        data = {
            'form': str(self.form.id),
            'label': 'Country',
            'field_type': 'select',
            'is_required': True,
            'options': {},  # Missing required choices
            'order_num': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('options', response.data)
    
    def test_list_fields(self):
        """Test listing user's fields."""
        # Create some fields
        Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        Field.objects.create(
            form=self.form,
            label='Field 2',
            field_type='email',
            order_num=2
        )
        
        # Create field for other user (should not appear)
        Field.objects.create(
            form=self.other_form,
            label='Other Field',
            field_type='text',
            order_num=1
        )
        
        url = '/api/v1/forms/fields/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_retrieve_field(self):
        """Test retrieving a specific field."""
        field = Field.objects.create(
            form=self.form,
            label='Test Field',
            field_type='text',
            order_num=1
        )
        
        url = f'/api/v1/forms/fields/{field.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['label'], 'Test Field')
    
    def test_retrieve_field_permission_denied(self):
        """Test retrieving field user doesn't own."""
        field = Field.objects.create(
            form=self.other_form,
            label='Other Field',
            field_type='text',
            order_num=1
        )
        
        url = f'/api/v1/forms/fields/{field.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_field(self):
        """Test updating a field."""
        field = Field.objects.create(
            form=self.form,
            label='Original Label',
            field_type='text',
            is_required=False,
            order_num=1
        )
        
        url = f'/api/v1/forms/fields/{field.id}/'
        data = {
            'label': 'Updated Label',
            'is_required': True
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        field.refresh_from_db()
        self.assertEqual(field.label, 'Updated Label')
        self.assertTrue(field.is_required)
    
    def test_delete_field(self):
        """Test deleting a field."""
        field = Field.objects.create(
            form=self.form,
            label='Test Field',
            field_type='text',
            order_num=1
        )
        
        url = f'/api/v1/forms/fields/{field.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Field.objects.filter(id=field.id).exists())
    
    def test_by_form_action(self):
        """Test the by_form custom action."""
        # Create fields for the form
        Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        Field.objects.create(
            form=self.form,
            label='Field 2',
            field_type='email',
            order_num=2
        )
        
        # Create field for other form
        Field.objects.create(
            form=self.other_form,
            label='Other Field',
            field_type='text',
            order_num=1
        )
        
        url = '/api/v1/forms/fields/by_form/'
        response = self.client.get(url, {'form_id': str(self.form.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_by_form_action_missing_form_id(self):
        """Test by_form action without form_id parameter."""
        url = '/api/v1/forms/fields/by_form/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('form_id', response.data['error'])
    
    def test_reorder_field(self):
        """Test field reordering."""
        field1 = Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        field2 = Field.objects.create(
            form=self.form,
            label='Field 2',
            field_type='text',
            order_num=2
        )
        field3 = Field.objects.create(
            form=self.form,
            label='Field 3',
            field_type='text',
            order_num=3
        )
        
        url = f'/api/v1/forms/fields/{field1.id}/reorder/'
        data = {'new_order': 3}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that orders were updated
        field1.refresh_from_db()
        field2.refresh_from_db()
        field3.refresh_from_db()
        
        self.assertEqual(field1.order_num, 3)
        self.assertEqual(field2.order_num, 1)
        self.assertEqual(field3.order_num, 2)
    
    def test_reorder_field_invalid_order(self):
        """Test field reordering with invalid order number."""
        field = Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        
        url = f'/api/v1/forms/fields/{field.id}/reorder/'
        data = {'new_order': 0}  # Invalid order
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_field_types_action(self):
        """Test getting available field types."""
        url = '/api/v1/forms/fields/field_types/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        # Check for specific field types
        field_type_values = [ft['value'] for ft in response.data]
        self.assertIn('text', field_type_values)
        self.assertIn('select', field_type_values)
        self.assertIn('rating', field_type_values)
    
    def test_my_fields_action(self):
        """Test the my_fields custom action."""
        # Create some fields
        Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        Field.objects.create(
            form=self.form,
            label='Field 2',
            field_type='email',
            order_num=2
        )
        
        url = '/api/v1/forms/fields/my_fields/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access endpoints."""
        self.client.credentials()  # Remove authentication
        
        url = '/api/v1/forms/fields/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
