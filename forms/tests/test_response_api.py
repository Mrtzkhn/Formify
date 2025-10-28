from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from forms.models import Form, Field, Response as FormResponse, Answer

User = get_user_model()


class ResponseAPITestCase(APITestCase):
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
        
        # Create test form with fields
        self.form = Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        
        self.text_field = Field.objects.create(
            form=self.form,
            label='Text Field',
            field_type='text',
            is_required=True,
            order_num=1
        )
        
        self.select_field = Field.objects.create(
            form=self.form,
            label='Select Field',
            field_type='select',
            is_required=False,
            options={'choices': ['Option 1', 'Option 2', 'Option 3']},
            order_num=2
        )
        
        # API URLs
        self.list_url = '/api/v1/forms/responses/'
        self.create_url = '/api/v1/forms/responses/'
        self.by_form_url = '/api/v1/forms/responses/by_form/'
        self.my_responses_url = '/api/v1/forms/responses/my_responses/'

    def test_submit_response_success(self):
        """Test successful response submission."""
        data = {
            'form': self.form.id,
            'answers': [
                {
                    'field_id': str(self.text_field.id),
                    'value': 'Test Answer'
                },
                {
                    'field_id': str(self.select_field.id),
                    'value': 'Option 1'
                }
            ]
        }
        
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FormResponse.objects.count(), 1)
        self.assertEqual(Answer.objects.count(), 2)
        
        response_obj = FormResponse.objects.first()
        self.assertEqual(response_obj.form, self.form)
        self.assertEqual(response_obj.submitted_by, self.user)

    def test_submit_response_missing_required_field(self):
        """Test response submission with missing required field."""
        data = {
            'form': self.form.id,
            'answers': [
                {
                    'field_id': str(self.select_field.id),
                    'value': 'Option 1'
                }
            ]
        }
        
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_submit_response_invalid_field_id(self):
        """Test response submission with invalid field ID."""
        data = {
            'form': self.form.id,
            'answers': [
                {
                    'field_id': 'invalid-field-id',
                    'value': 'Test Answer'
                }
            ]
        }
        
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_submit_response_to_inactive_form(self):
        """Test response submission to inactive form."""
        self.form.is_active = False
        self.form.save()
        
        data = {
            'form': self.form.id,
            'answers': [
                {
                    'field_id': str(self.text_field.id),
                    'value': 'Test Answer'
                }
            ]
        }
        
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('form', response.data)

    def test_list_responses(self):
        """Test listing form owner responses."""
        # Create responses
        response1 = FormResponse.objects.create(
            form=self.form,
            submitted_by=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        Answer.objects.create(
            response=response1,
            field=self.text_field,
            value='Answer 1'
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['form_title'], 'Test Form')

    def test_retrieve_response_success(self):
        """Test successful response retrieval."""
        response_obj = FormResponse.objects.create(
            form=self.form,
            submitted_by=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        Answer.objects.create(
            response=response_obj,
            field=self.text_field,
            value='Test Answer'
        )
        
        url = f'/api/v1/forms/responses/{response_obj.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['form_title'], 'Test Form')
        self.assertEqual(response.data['answer_count'], 1)

    def test_retrieve_response_other_user(self):
        """Test retrieving response from another user's form."""
        other_form = Form.objects.create(
            title='Other Form',
            description='Other Description',
            created_by=self.other_user
        )
        
        response_obj = FormResponse.objects.create(
            form=other_form,
            submitted_by=self.other_user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        url = f'/api/v1/forms/responses/{response_obj.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_by_form_action(self):
        """Test the by_form custom action."""
        response_obj = FormResponse.objects.create(
            form=self.form,
            submitted_by=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        url = f'{self.by_form_url}?form_id={self.form.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['form_title'], 'Test Form')

    def test_by_form_action_missing_form_id(self):
        """Test by_form action without form_id parameter."""
        url = self.by_form_url
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_my_responses_action(self):
        """Test the my_responses custom action."""
        response_obj = FormResponse.objects.create(
            form=self.form,
            submitted_by=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        response = self.client.get(self.my_responses_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['form_title'], 'Test Form')

    def test_delete_response_success(self):
        """Test successful response deletion."""
        response_obj = FormResponse.objects.create(
            form=self.form,
            submitted_by=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        url = f'/api/v1/forms/responses/{response_obj.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FormResponse.objects.count(), 0)

    def test_delete_response_other_user(self):
        """Test deleting response from another user's form."""
        other_form = Form.objects.create(
            title='Other Form',
            description='Other Description',
            created_by=self.other_user
        )
        
        response_obj = FormResponse.objects.create(
            form=other_form,
            submitted_by=self.other_user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        url = f'/api/v1/forms/responses/{response_obj.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access endpoints."""
        self.client.logout()
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post(self.create_url, {'form': self.form.id, 'answers': []})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AnswerAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.form = Form.objects.create(
            title='Test Form',
            description='Test Description',
            created_by=self.user
        )
        
        self.field = Field.objects.create(
            form=self.form,
            label='Test Field',
            field_type='text',
            is_required=True,
            order_num=1
        )
        
        self.response = FormResponse.objects.create(
            form=self.form,
            submitted_by=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.answer = Answer.objects.create(
            response=self.response,
            field=self.field,
            value='Test Answer'
        )
        
        # API URLs
        self.list_url = '/api/v1/forms/answers/'
        self.by_response_url = '/api/v1/forms/answers/by_response/'
        self.by_field_url = '/api/v1/forms/answers/by_field/'
        self.field_statistics_url = '/api/v1/forms/answers/field_statistics/'

    def test_list_answers(self):
        """Test listing answers."""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['field_label'], 'Test Field')

    def test_retrieve_answer_success(self):
        """Test successful answer retrieval."""
        url = f'/api/v1/forms/answers/{self.answer.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['field_label'], 'Test Field')
        self.assertEqual(response.data['value'], 'Test Answer')

    def test_by_response_action(self):
        """Test the by_response custom action."""
        url = f'{self.by_response_url}?response_id={self.response.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['field_label'], 'Test Field')

    def test_by_response_action_missing_response_id(self):
        """Test by_response action without response_id parameter."""
        url = self.by_response_url
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_by_field_action(self):
        """Test the by_field custom action."""
        url = f'{self.by_field_url}?field_id={self.field.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['field_label'], 'Test Field')

    def test_by_field_action_missing_field_id(self):
        """Test by_field action without field_id parameter."""
        url = self.by_field_url
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_field_statistics_action(self):
        """Test the field_statistics custom action."""
        url = f'{self.field_statistics_url}?field_id={self.field.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_answers'], 1)
        self.assertEqual(response.data['unique_values'], 1)
        self.assertEqual(response.data['most_common_value'], 'Test Answer')

    def test_field_statistics_action_missing_field_id(self):
        """Test field_statistics action without field_id parameter."""
        url = self.field_statistics_url
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
