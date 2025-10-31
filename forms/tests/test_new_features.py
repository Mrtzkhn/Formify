from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from forms.models import Form, Field, Process, ProcessStep

User = get_user_model()


class FormManagementAPITestCase(APITestCase):
    """Test cases for the new form management API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # API URLs
        self.forms_url = '/api/v1/forms/'
        self.public_forms_url = '/api/v1/forms/public/forms/'
        self.private_forms_url = '/api/v1/forms/private/forms/validate/'

    def test_create_form_success(self):
        """Test successful form creation."""
        data = {
            'title': 'Test Form',
            'description': 'Test Description',
            'is_public': True,
            'is_active': True
        }
        
        response = self.client.post(self.forms_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        
        form = Form.objects.first()
        self.assertEqual(form.title, 'Test Form')
        self.assertEqual(form.created_by, self.user)
        self.assertTrue(form.is_public)

    def test_create_private_form_with_password(self):
        """Test creating a private form with password."""
        data = {
            'title': 'Private Form',
            'description': 'Private Description',
            'is_public': False,
            'access_password': 'secret123',
            'is_active': True
        }
        
        response = self.client.post(self.forms_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        form = Form.objects.first()
        self.assertFalse(form.is_public)
        self.assertEqual(form.access_password, 'secret123')

    def test_list_user_forms(self):
        """Test listing user's forms."""
        # Create a form
        Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        
        response = self.client.get(self.forms_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Form')

    def test_public_form_access(self):
        """Test accessing public forms."""
        # Create a public form
        form = Form.objects.create(
            title='Public Form',
            description='Public Description',
            created_by=self.user,
            is_public=True
        )
        
        # Create a field for the form
        Field.objects.create(
            form=form,
            label='Test Field',
            field_type='text',
            is_required=True,
            order_num=1
        )
        
        # Access public form without authentication
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/v1/forms/public/forms/{form.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Public Form')

    def test_private_form_password_validation(self):
        """Test private form password validation."""
        # Create a private form
        form = Form.objects.create(
            title='Private Form',
            description='Private Description',
            created_by=self.user,
            is_public=False,
            access_password='secret123'
        )
        
        # Test with correct password
        data = {
            'form_id': str(form.id),
            'password': 'secret123'
        }
        
        response = self.client.post(self.private_forms_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Private Form')

    def test_private_form_invalid_password(self):
        """Test private form with invalid password."""
        # Create a private form
        form = Form.objects.create(
            title='Private Form',
            description='Private Description',
            created_by=self.user,
            is_public=False,
            access_password='secret123'
        )
        
        # Test with incorrect password
        data = {
            'form_id': str(form.id),
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.private_forms_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid password', response.data['detail'])


class ProcessWorkflowAPITestCase(APITestCase):
    """Test cases for process workflow API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        
        # Create a form
        self.form = Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        
        # Create a field
        self.field = Field.objects.create(
            form=self.form,
            label='Test Field',
            field_type='text',
            is_required=True,
            order_num=1
        )
        
        # Create a process
        self.process = Process.objects.create(
            title='Test Process',
            description='Test Process Description',
            process_type='linear',
            created_by=self.user,
            is_public=True
        )
        
        # Create a process step
        self.process_step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Step 1',
            step_description='First step',
            order_num=1,
            is_mandatory=True
        )
        
        # API URLs
        self.workflow_urls = {
            'process_steps': '/api/v1/forms/workflow/process-steps/',
            'current_step': '/api/v1/forms/workflow/current-step/',
            'complete_step': '/api/v1/forms/workflow/complete-step/',
            'progress': '/api/v1/forms/workflow/progress/'
        }

    def test_get_process_steps(self):
        """Test getting process steps."""
        response = self.client.get(
            self.workflow_urls['process_steps'],
            {'process_id': str(self.process.id)}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['steps']), 1)
        self.assertEqual(response.data['steps'][0]['step_name'], 'Step 1')

    def test_get_current_step_linear_process(self):
        """Test getting current step for linear process."""
        response = self.client.get(
            self.workflow_urls['current_step'],
            {'process_id': str(self.process.id)}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_completed'])
        self.assertEqual(response.data['current_step']['step_name'], 'Step 1')

    def test_complete_process_step(self):
        """Test completing a process step."""
        data = {
            'step_id': str(self.process_step.id),
            'answers': [
                {
                    'field_id': str(self.field.id),
                    'value': 'Test Answer'
                }
            ]
        }
        
        response = self.client.post(self.workflow_urls['complete_step'], data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['response'])

    def test_get_process_progress(self):
        """Test getting process progress."""
        response = self.client.get(
            self.workflow_urls['progress'],
            {'process_id': str(self.process.id)}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['progress']['total_steps'], 1)
        self.assertEqual(response.data['progress']['completed_steps'], 0)
        self.assertFalse(response.data['progress']['is_complete'])
