from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError

from forms.models import Form, Field
from forms.services.services import FieldService

User = get_user_model()


class FieldServiceTestCase(TestCase):
    """Test cases for FieldService business logic."""
    
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
        self.field_service = FieldService()
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
    
    def test_create_field_success(self):
        """Test successful field creation."""
        field_data = {
            'label': 'Test Field',
            'field_type': 'text',
            'is_required': True,
            'options': {},
            'order_num': 1
        }
        
        field = self.field_service.create_field(
            user=self.user,
            form_id=str(self.form.id),
            field_data=field_data
        )
        
        self.assertEqual(field.label, 'Test Field')
        self.assertEqual(field.field_type, 'text')
        self.assertTrue(field.is_required)
        self.assertEqual(field.form, self.form)
        self.assertEqual(field.order_num, 1)
    
    def test_create_field_permission_denied(self):
        """Test field creation with permission denied."""
        field_data = {
            'label': 'Test Field',
            'field_type': 'text',
            'is_required': True,
            'options': {},
            'order_num': 1
        }
        
        with self.assertRaises(Exception):  # Should raise 404 (form not found)
            FieldService.create_field(
                user=self.user,
                form_id=str(self.other_form.id),
                field_data=field_data
            )
    
    def test_create_field_auto_order(self):
        """Test field creation with automatic order assignment."""
        # Create first field
        Field.objects.create(
            form=self.form,
            label='First Field',
            field_type='text',
            order_num=1
        )
        
        field_data = {
            'label': 'Second Field',
            'field_type': 'text',
            'is_required': False,
            'options': {}
        }
        
        field = self.field_service.create_field(
            user=self.user,
            form_id=str(self.form.id),
            field_data=field_data
        )
        
        self.assertEqual(field.order_num, 2)
    
    def test_get_user_fields(self):
        """Test getting all fields for user's forms."""
        # Create fields for user's form
        field1 = Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        field2 = Field.objects.create(
            form=self.form,
            label='Field 2',
            field_type='email',
            order_num=2
        )
        
        # Create field for other user's form (should not be included)
        Field.objects.create(
            form=self.other_form,
            label='Other Field',
            field_type='text',
            order_num=1
        )
        
        fields = self.field_service.get_user_fields(self.user)
        
        self.assertEqual(len(fields), 2)
        self.assertIn(field1, fields)
        self.assertIn(field2, fields)
    
    def test_get_form_fields(self):
        """Test getting fields for a specific form."""
        field1 = Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        field2 = Field.objects.create(
            form=self.form,
            label='Field 2',
            field_type='email',
            order_num=2
        )
        
        fields = self.field_service.get_form_fields(
            user=self.user,
            form_id=str(self.form.id)
        )
        
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0], field1)
        self.assertEqual(fields[1], field2)
    
    def test_get_form_fields_permission_denied(self):
        """Test getting fields for form user doesn't own."""
        with self.assertRaises(Exception):  # Should raise 404
            FieldService.get_form_fields(
                user=self.user,
                form_id=str(self.other_form.id)
            )
    
    def test_update_field_success(self):
        """Test successful field update."""
        field = Field.objects.create(
            form=self.form,
            label='Original Label',
            field_type='text',
            is_required=False,
            order_num=1
        )
        
        field_data = {
            'label': 'Updated Label',
            'is_required': True
        }
        
        updated_field = self.field_service.update_field(
            user=self.user,
            field_id=str(field.id),
            field_data=field_data
        )
        
        self.assertEqual(updated_field.label, 'Updated Label')
        self.assertTrue(updated_field.is_required)
        self.assertEqual(updated_field.field_type, 'text')  # Unchanged
    
    def test_update_field_permission_denied(self):
        """Test field update with permission denied."""
        field = Field.objects.create(
            form=self.other_form,
            label='Other Field',
            field_type='text',
            order_num=1
        )
        
        with self.assertRaises(Exception):  # Should raise 404
            FieldService.update_field(
                user=self.user,
                field_id=str(field.id),
                field_data={'label': 'Updated'}
            )
    
    def test_delete_field_success(self):
        """Test successful field deletion."""
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
        
        # Delete field2 (middle field)
        result = self.field_service.delete_field(
            user=self.user,
            field_id=str(field2.id)
        )
        
        self.assertTrue(result)
        
        # Check that field2 is deleted
        self.assertFalse(Field.objects.filter(id=field2.id).exists())
        
        # Check that field3's order_num is decremented
        field3.refresh_from_db()
        self.assertEqual(field3.order_num, 2)
    
    def test_delete_field_permission_denied(self):
        """Test field deletion with permission denied."""
        field = Field.objects.create(
            form=self.other_form,
            label='Other Field',
            field_type='text',
            order_num=1
        )
        
        with self.assertRaises(Exception):  # Should raise 404
            FieldService.delete_field(
                user=self.user,
                field_id=str(field.id)
            )
    
    def test_reorder_field_success(self):
        """Test successful field reordering."""
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
        
        # Move field1 to position 3
        updated_field = self.field_service.reorder_field(
            user=self.user,
            field_id=str(field1.id),
            new_order=3
        )
        
        # Refresh all fields from database
        field1.refresh_from_db()
        field2.refresh_from_db()
        field3.refresh_from_db()
        
        self.assertEqual(field1.order_num, 3)
        self.assertEqual(field2.order_num, 1)  # Moved up
        self.assertEqual(field3.order_num, 2)  # Moved up
    
    def test_reorder_field_invalid_order(self):
        """Test field reordering with invalid order number."""
        field = Field.objects.create(
            form=self.form,
            label='Field 1',
            field_type='text',
            order_num=1
        )
        
        with self.assertRaises(ValidationError):
            self.field_service.reorder_field(
                user=self.user,
                field_id=str(field.id),
                new_order=0  # Invalid order
            )
    
    def test_validate_field_options_select(self):
        """Test validation of select field options."""
        # Valid select options
        valid_options = {
            'choices': [
                {'value': 'option1', 'label': 'Option 1'},
                {'value': 'option2', 'label': 'Option 2'}
            ]
        }
        
        self.assertTrue(
            self.field_service.validate_field_options('select', valid_options)
        )
        
        # Invalid select options (no choices)
        invalid_options = {}
        
        with self.assertRaises(ValidationError):
            self.field_service.validate_field_options('select', invalid_options)
    
    def test_validate_field_options_rating(self):
        """Test validation of rating field options."""
        # Valid rating options
        valid_options = {
            'min_value': 1,
            'max_value': 5,
            'step': 1
        }
        
        self.assertTrue(
            self.field_service.validate_field_options('rating', valid_options)
        )
        
        # Invalid rating options (min >= max)
        invalid_options = {
            'min_value': 5,
            'max_value': 3
        }
        
        with self.assertRaises(ValidationError):
            self.field_service.validate_field_options('rating', invalid_options)
    
    def test_validate_field_options_file(self):
        """Test validation of file field options."""
        # Valid file options
        valid_options = {
            'allowed_types': ['image/jpeg', 'image/png'],
            'max_size': 5242880  # 5MB
        }
        
        self.assertTrue(
            self.field_service.validate_field_options('file', valid_options)
        )
        
        # Invalid file options (no allowed_types)
        invalid_options = {
            'max_size': 5242880
        }
        
        with self.assertRaises(ValidationError):
            self.field_service.validate_field_options('file', invalid_options)
    
    def test_get_field_types(self):
        """Test getting available field types."""
        field_types = self.field_service.get_field_types()
        
        self.assertIsInstance(field_types, list)
        self.assertGreater(len(field_types), 0)
        
        # Check that each field type has value and label
        for field_type in field_types:
            self.assertIn('value', field_type)
            self.assertIn('label', field_type)
        
        # Check for specific field types
        field_type_values = [ft['value'] for ft in field_types]
        self.assertIn('text', field_type_values)
        self.assertIn('select', field_type_values)
        self.assertIn('rating', field_type_values)
