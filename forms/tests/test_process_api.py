from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from forms.models import Form, Process, ProcessStep

User = get_user_model()


class ProcessAPITestCase(APITestCase):
    """Test cases for Process API endpoints."""

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
        self.client.force_authenticate(user=self.user)
        
        # API URLs
        self.list_url = '/api/v1/forms/processes/'
        self.create_url = '/api/v1/forms/processes/'
        self.process_types_url = '/api/v1/forms/processes/process_types/'
        self.my_processes_url = '/api/v1/forms/processes/my_processes/'
        self.public_processes_url = '/api/v1/forms/processes/public_processes/'

    def test_create_process_success(self):
        """Test successful process creation."""
        data = {
            'title': 'Test Process',
            'description': 'Test Process Description',
            'process_type': 'linear',
            'is_public': True
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Process.objects.count(), 1)
        
        process = Process.objects.first()
        self.assertEqual(process.title, 'Test Process')
        self.assertEqual(process.process_type, 'linear')
        self.assertEqual(process.created_by, self.user)

    def test_create_process_invalid_type(self):
        """Test process creation with invalid type."""
        data = {
            'title': 'Test Process',
            'description': 'Test Process Description',
            'process_type': 'invalid_type',
            'is_public': True
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('process_type', response.data)

    def test_create_process_private_without_password(self):
        """Test creating private process without password."""
        data = {
            'title': 'Private Process',
            'description': 'Private Process Description',
            'process_type': 'linear',
            'is_public': False
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('access_password', response.data)

    def test_list_processes(self):
        """Test listing user's processes."""
        # Create processes for both users
        Process.objects.create(
            title='User Process',
            description='User Description',
            process_type='linear',
            created_by=self.user
        )
        Process.objects.create(
            title='Other Process',
            description='Other Description',
            process_type='free',
            created_by=self.other_user
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'User Process')

    def test_get_process_detail(self):
        """Test getting process detail."""
        process = Process.objects.create(
            title='Test Process',
            description='Test Description',
            process_type='linear',
            created_by=self.user
        )
        
        url = f'/api/v1/forms/processes/{process.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Process')
        self.assertEqual(response.data['process_type'], 'linear')

    def test_update_process_success(self):
        """Test successful process update."""
        process = Process.objects.create(
            title='Original Process',
            description='Original Description',
            process_type='linear',
            created_by=self.user
        )
        
        data = {
            'title': 'Updated Process',
            'description': 'Updated Description',
            'process_type': 'free',
            'is_public': True,
            'access_password': ''
        }
        
        url = f'/api/v1/forms/processes/{process.id}/'
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        process.refresh_from_db()
        self.assertEqual(process.title, 'Updated Process')
        self.assertEqual(process.process_type, 'free')

    def test_delete_process_success(self):
        """Test successful process deletion."""
        process = Process.objects.create(
            title='Test Process',
            description='Test Description',
            process_type='linear',
            created_by=self.user
        )
        
        url = f'/api/v1/forms/processes/{process.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Process.objects.filter(id=process.id).exists())

    def test_process_types_action(self):
        """Test getting available process types."""
        response = self.client.get(self.process_types_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)
        
        type_values = [pt['value'] for pt in response.data]
        self.assertIn('linear', type_values)
        self.assertIn('free', type_values)

    def test_my_processes_action(self):
        """Test the my_processes custom action."""
        # Create processes for both users
        Process.objects.create(
            title='User Process',
            description='User Description',
            process_type='linear',
            created_by=self.user
        )
        Process.objects.create(
            title='Other Process',
            description='Other Description',
            process_type='free',
            created_by=self.other_user
        )
        
        response = self.client.get(self.my_processes_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'User Process')

    def test_public_processes_action(self):
        """Test the public_processes custom action."""
        # Create public and private processes
        Process.objects.create(
            title='Public Process',
            description='Public Description',
            process_type='linear',
            is_public=True,
            created_by=self.user
        )
        Process.objects.create(
            title='Private Process',
            description='Private Description',
            process_type='free',
            is_public=False,
            access_password='password123',
            created_by=self.user
        )
        
        response = self.client.get(self.public_processes_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Public Process')


class ProcessStepAPITestCase(APITestCase):
    """Test cases for ProcessStep API endpoints."""

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
        self.process = Process.objects.create(
            title='Test Process',
            description='Test Description',
            process_type='linear',
            created_by=self.user
        )
        self.form = Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)
        
        # API URLs
        self.list_url = '/api/v1/forms/process-steps/'
        self.create_url = '/api/v1/forms/process-steps/'
        self.by_process_url = '/api/v1/forms/process-steps/by_process/'
        self.my_steps_url = '/api/v1/forms/process-steps/my_steps/'

    def test_create_process_step_success(self):
        """Test successful process step creation."""
        data = {
            'process': self.process.id,
            'form': self.form.id,
            'step_name': 'Step 1',
            'step_description': 'First step',
            'order_num': 1,
            'is_required': True
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProcessStep.objects.count(), 1)
        
        step = ProcessStep.objects.first()
        self.assertEqual(step.step_name, 'Step 1')
        self.assertEqual(step.form, self.form)
        self.assertEqual(step.process, self.process)

    def test_create_process_step_other_user_form(self):
        """Test creating process step with form from another user."""
        other_form = Form.objects.create(
            title='Other Form',
            description='Other Description',
            created_by=self.other_user
        )
        
        data = {
            'process': self.process.id,
            'form': other_form.id,
            'step_name': 'Step 1',
            'step_description': 'First step',
            'order_num': 1,
            'is_required': True
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('form', response.data)

    def test_list_process_steps(self):
        """Test listing user's process steps."""
        # Create process steps
        ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Step 1',
            order_num=1
        )
        
        # Create process step for other user's process
        other_process = Process.objects.create(
            title='Other Process',
            description='Other Description',
            process_type='free',
            created_by=self.other_user
        )
        other_form = Form.objects.create(
            title='Other Form',
            description='Other Description',
            created_by=self.other_user
        )
        ProcessStep.objects.create(
            process=other_process,
            form=other_form,
            step_name='Other Step',
            order_num=1
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['step_name'], 'Step 1')

    def test_get_process_step_detail(self):
        """Test getting process step detail."""
        step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Test Step',
            order_num=1
        )
        
        url = f'/api/v1/forms/process-steps/{step.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['step_name'], 'Test Step')

    def test_update_process_step_success(self):
        """Test successful process step update."""
        step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Original Step',
            order_num=1
        )
        
        data = {
            'step_name': 'Updated Step',
            'step_description': 'Updated Description'
        }
        
        url = f'/api/v1/forms/process-steps/{step.id}/'
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        step.refresh_from_db()
        self.assertEqual(step.step_name, 'Updated Step')
        self.assertEqual(step.step_description, 'Updated Description')

    def test_delete_process_step_success(self):
        """Test successful process step deletion."""
        step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Test Step',
            order_num=1
        )
        
        url = f'/api/v1/forms/process-steps/{step.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProcessStep.objects.filter(id=step.id).exists())

    def test_by_process_action(self):
        """Test the by_process custom action."""
        # Create process steps
        ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Step 1',
            order_num=1
        )
        ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Step 2',
            order_num=2
        )
        
        url = f'{self.by_process_url}?process_id={self.process.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['step_name'], 'Step 1')
        self.assertEqual(response.data[1]['step_name'], 'Step 2')

    def test_reorder_process_step_success(self):
        """Test successful process step reordering."""
        step1 = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Step 1',
            order_num=1
        )
        step2 = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Step 2',
            order_num=2
        )
        
        data = {'new_order': 2}
        url = f'/api/v1/forms/process-steps/{step1.id}/reorder/'
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        step1.refresh_from_db()
        step2.refresh_from_db()
        
        self.assertEqual(step1.order_num, 2)
        self.assertEqual(step2.order_num, 1)

    def test_my_steps_action(self):
        """Test the my_steps custom action."""
        # Create process steps
        ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            step_name='Step 1',
            order_num=1
        )
        
        # Create process step for other user's process
        other_process = Process.objects.create(
            title='Other Process',
            description='Other Description',
            process_type='free',
            created_by=self.other_user
        )
        other_form = Form.objects.create(
            title='Other Form',
            description='Other Description',
            created_by=self.other_user
        )
        ProcessStep.objects.create(
            process=other_process,
            form=other_form,
            step_name='Other Step',
            order_num=1
        )
        
        response = self.client.get(self.my_steps_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['step_name'], 'Step 1')
