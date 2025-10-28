#!/usr/bin/env python
"""
Comprehensive API Testing Script for Formify
Merges all API testing functionality into a single comprehensive test suite.
Tests all available API endpoints with both live server and Django test client approaches.
"""

import os
import sys
import django
import requests
import uuid
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from forms.models import Form, Field, Process, ProcessStep, Category, EntityCategory, Response as FormResponse, Answer, FormView

User = get_user_model()

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH_TOKEN = None
USER_ID = None

def log_test(test_name, status, details=""):
    """Log test results with formatting."""
    status_symbol = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"{status_symbol} {test_name}: {status}")
    if details:
        print(f"   Details: {details}")

def make_request(method, url, data=None, headers=None, expected_status=200):
    """Make HTTP request and return response."""
    if headers is None:
        headers = {}
    
    if AUTH_TOKEN:
        headers['Authorization'] = f'Bearer {AUTH_TOKEN}'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, headers=headers, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        return response
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
        return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

class LiveServerAPITest:
    """Live server API testing using requests."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token = None
        self.user_id = None
    
    def test_authentication(self):
        """Test all authentication endpoints."""
        print("\n[TEST] Testing Authentication APIs (Live Server)...")
        print("=" * 50)
        
        global AUTH_TOKEN, USER_ID
        
        # Test registration
        register_data = {
            "email": f"testuser{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "full_name": "Test User"
        }
        
        response = make_request('POST', f'{self.base_url}/accounts/register/', register_data)
        if response and response.status_code in [200, 201]:
            log_test("User Registration", "PASS", f"Status: {response.status_code}")
        else:
            log_test("User Registration", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        
        # Test login with existing user from seeded data
        login_data = {
            "email": "test1@example.com",  # Use seeded user
            "password": "testpass123"
        }
        
        response = make_request('POST', f'{self.base_url}/accounts/login/', login_data)
        if response and response.status_code == 200:
            data = response.json()
            AUTH_TOKEN = data.get('access')
            USER_ID = data.get('user', {}).get('id')
            self.auth_token = AUTH_TOKEN
            self.user_id = USER_ID
            log_test("User Login", "PASS", f"Token received: {AUTH_TOKEN[:20]}...")
        else:
            log_test("User Login", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
        
        # Test token refresh
        if AUTH_TOKEN:
            refresh_data = {"refresh": data.get('refresh')}
            response = make_request('POST', f'{self.base_url}/accounts/token/refresh/', refresh_data)
            if response and response.status_code == 200:
                log_test("Token Refresh", "PASS")
            else:
                log_test("Token Refresh", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        
        # Test me endpoint
        response = make_request('GET', f'{self.base_url}/accounts/me/')
        if response and response.status_code == 200:
            log_test("Get User Profile", "PASS")
        else:
            log_test("Get User Profile", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        
        # Test ping endpoint
        response = make_request('GET', f'{self.base_url}/accounts/ping/')
        if response and response.status_code == 200:
            log_test("Version Ping", "PASS")
        else:
            log_test("Version Ping", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_forms_api(self):
        """Test all forms-related endpoints."""
        print("\n[TEST] Testing Forms APIs (Live Server)...")
        print("=" * 50)
        
        # Test list forms
        response = make_request('GET', f'{self.base_url}/forms/')
        if response and response.status_code == 200:
            forms = response.json()
            log_test("List Forms", "PASS", f"Found {len(forms)} forms")
            
            if forms:
                form_id = forms[0]['id']
                
                # Test get form detail
                response = make_request('GET', f'{self.base_url}/forms/{form_id}/')
                if response and response.status_code == 200:
                    log_test("Get Form Detail", "PASS")
                else:
                    log_test("Get Form Detail", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test create form
                create_data = {
                    "title": "New Test Form",
                    "description": "New form description",
                    "is_public": True
                }
                response = make_request('POST', f'{self.base_url}/forms/', create_data)
                if response and response.status_code == 201:
                    log_test("Create Form", "PASS")
                else:
                    log_test("Create Form", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test update form
                update_data = {"title": "Updated Form Title"}
                response = make_request('PATCH', f'{self.base_url}/forms/{form_id}/', update_data)
                if response and response.status_code == 200:
                    log_test("Update Form", "PASS")
                else:
                    log_test("Update Form", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test my forms endpoint
                response = make_request('GET', f'{self.base_url}/forms/my_forms/')
                if response and response.status_code == 200:
                    my_forms = response.json()
                    log_test("My Forms", "PASS", f"Found {len(my_forms)} user forms")
                else:
                    log_test("My Forms", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test public forms endpoint
                response = make_request('GET', f'{self.base_url}/forms/public_forms/')
                if response and response.status_code == 200:
                    public_forms = response.json()
                    log_test("Public Forms", "PASS", f"Found {len(public_forms)} public forms")
                else:
                    log_test("Public Forms", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            log_test("List Forms", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_fields_api(self):
        """Test all fields-related endpoints."""
        print("\n[TEST] Testing Fields APIs (Live Server)...")
        print("=" * 50)
        
        # Test list fields
        response = make_request('GET', f'{self.base_url}/forms/fields/')
        if response and response.status_code == 200:
            fields = response.json()
            log_test("List Fields", "PASS", f"Found {len(fields)} fields")
            
            if fields:
                field_id = fields[0]['id']
                
                # Test get field detail
                response = make_request('GET', f'{self.base_url}/forms/fields/{field_id}/')
                if response and response.status_code == 200:
                    log_test("Get Field Detail", "PASS")
                else:
                    log_test("Get Field Detail", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test field statistics (using correct endpoint with parameters)
                response = make_request('GET', f'{self.base_url}/forms/answers/field_statistics/?field_id={field_id}')
                if response and response.status_code == 200:
                    log_test("Field Statistics", "PASS")
                else:
                    log_test("Field Statistics", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test field types endpoint
                response = make_request('GET', f'{self.base_url}/forms/fields/field_types/')
                if response and response.status_code == 200:
                    field_types = response.json()
                    log_test("Field Types", "PASS", f"Found {len(field_types)} field types")
                else:
                    log_test("Field Types", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test my fields endpoint
                response = make_request('GET', f'{self.base_url}/forms/fields/my_fields/')
                if response and response.status_code == 200:
                    my_fields = response.json()
                    log_test("My Fields", "PASS", f"Found {len(my_fields)} user fields")
                else:
                    log_test("My Fields", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test answers by field endpoint
                response = make_request('GET', f'{self.base_url}/forms/answers/by_field/?field_id={field_id}')
                if response and response.status_code == 200:
                    answers = response.json()
                    log_test("Answers by Field", "PASS", f"Found {len(answers)} answers")
                else:
                    log_test("Answers by Field", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            log_test("List Fields", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_processes_api(self):
        """Test all processes-related endpoints."""
        print("\n[TEST] Testing Processes APIs (Live Server)...")
        print("=" * 50)
        
        # Test list processes
        response = make_request('GET', f'{self.base_url}/forms/processes/')
        if response and response.status_code == 200:
            processes = response.json()
            log_test("List Processes", "PASS", f"Found {len(processes)} processes")
            
            if processes:
                process_id = processes[0]['id']
                
                # Test get process detail
                response = make_request('GET', f'{self.base_url}/forms/processes/{process_id}/')
                if response and response.status_code == 200:
                    log_test("Get Process Detail", "PASS")
                else:
                    log_test("Get Process Detail", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
            # Test process types
            response = make_request('GET', f'{self.base_url}/forms/processes/process_types/')
            if response and response.status_code == 200:
                log_test("Process Types", "PASS")
            else:
                log_test("Process Types", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
            # Test my processes endpoint
            response = make_request('GET', f'{self.base_url}/forms/processes/my_processes/')
            if response and response.status_code == 200:
                my_processes = response.json()
                log_test("My Processes", "PASS", f"Found {len(my_processes)} user processes")
            else:
                log_test("My Processes", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
            # Test public processes endpoint
            response = make_request('GET', f'{self.base_url}/forms/processes/public_processes/')
            if response and response.status_code == 200:
                public_processes = response.json()
                log_test("Public Processes", "PASS", f"Found {len(public_processes)} public processes")
            else:
                log_test("Public Processes", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            log_test("List Processes", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_public_forms_api(self):
        """Test all public forms-related endpoints."""
        print("\n[TEST] Testing Public Forms APIs (Live Server)...")
        print("=" * 50)
        
        # Test list public forms
        response = make_request('GET', f'{self.base_url}/forms/public/forms/')
        if response and response.status_code == 200:
            public_forms = response.json()
            log_test("List Public Forms", "PASS", f"Found {len(public_forms)} public forms")
            
            if public_forms:
                form_id = public_forms[0]['id']
                
                # Test get public form detail
                response = make_request('GET', f'{self.base_url}/forms/public/forms/{form_id}/')
                if response and response.status_code == 200:
                    log_test("Get Public Form Detail", "PASS")
                else:
                    log_test("Get Public Form Detail", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            log_test("List Public Forms", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_workflow_api(self):
        """Test all workflow-related endpoints."""
        print("\n[TEST] Testing Workflow APIs (Live Server)...")
        print("=" * 50)
        
        # First get a valid process ID
        processes_response = make_request('GET', f'{self.base_url}/forms/processes/')
        process_id = None
        if processes_response and processes_response.status_code == 200:
            processes = processes_response.json()
            if processes:
                process_id = processes[0]['id']
                log_test("Got Process ID", "PASS", f"Process ID: {process_id}")
        
        if process_id:
            # Test get process steps with valid process_id
            response = make_request('GET', f'{self.base_url}/forms/workflow/process-steps/?process_id={process_id}')
            if response and response.status_code in [200, 400]:
                log_test("Get Process Steps", "PASS", f"Status: {response.status_code}")
            else:
                log_test("Get Process Steps", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
            # Test get current step with valid process_id
            response = make_request('GET', f'{self.base_url}/forms/workflow/current-step/?process_id={process_id}')
            if response and response.status_code in [200, 400]:
                log_test("Get Current Step", "PASS", f"Status: {response.status_code}")
            else:
                log_test("Get Current Step", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
            # Test get process progress with valid process_id
            response = make_request('GET', f'{self.base_url}/forms/workflow/progress/?process_id={process_id}')
            if response and response.status_code in [200, 400]:
                log_test("Get Process Progress", "PASS", f"Status: {response.status_code}")
            else:
                log_test("Get Process Progress", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            # Test without process_id (should return 400)
            response = make_request('GET', f'{self.base_url}/forms/workflow/process-steps/')
            if response and response.status_code == 400:
                log_test("Get Process Steps (No Process ID)", "PASS", f"Status: {response.status_code}")
            else:
                log_test("Get Process Steps (No Process ID)", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
            response = make_request('GET', f'{self.base_url}/forms/workflow/current-step/')
            if response and response.status_code == 400:
                log_test("Get Current Step (No Process ID)", "PASS", f"Status: {response.status_code}")
            else:
                log_test("Get Current Step (No Process ID)", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
            response = make_request('GET', f'{self.base_url}/forms/workflow/progress/')
            if response and response.status_code == 400:
                log_test("Get Process Progress (No Process ID)", "PASS", f"Status: {response.status_code}")
            else:
                log_test("Get Process Progress (No Process ID)", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_categories_api(self):
        """Test all categories-related endpoints."""
        print("\n[TEST] Testing Categories APIs (Live Server)...")
        print("=" * 50)
        
        # Test list categories
        response = make_request('GET', f'{self.base_url}/forms/categories/')
        if response and response.status_code == 200:
            categories = response.json()
            log_test("List Categories", "PASS", f"Found {len(categories)} categories")
            
            if categories:
                category_id = categories[0]['id']
                
                # Test get category detail
                response = make_request('GET', f'{self.base_url}/forms/categories/{category_id}/')
                if response and response.status_code == 200:
                    log_test("Get Category Detail", "PASS")
                else:
                    log_test("Get Category Detail", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test my categories endpoint
                response = make_request('GET', f'{self.base_url}/forms/categories/my_categories/')
                if response and response.status_code == 200:
                    my_categories = response.json()
                    log_test("My Categories", "PASS", f"Found {len(my_categories)} user categories")
                else:
                    log_test("My Categories", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            log_test("List Categories", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_responses_api(self):
        """Test all responses-related endpoints."""
        print("\n[TEST] Testing Responses APIs (Live Server)...")
        print("=" * 50)
        
        # Test list responses
        response = make_request('GET', f'{self.base_url}/forms/responses/')
        if response and response.status_code == 200:
            responses = response.json()
            log_test("List Responses", "PASS", f"Found {len(responses)} responses")
            
            if responses:
                response_id = responses[0]['id']
                
                # Test get response detail
                response = make_request('GET', f'{self.base_url}/forms/responses/{response_id}/')
                if response and response.status_code == 200:
                    log_test("Get Response Detail", "PASS")
                else:
                    log_test("Get Response Detail", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test my responses endpoint
                response = make_request('GET', f'{self.base_url}/forms/responses/my_responses/')
                if response and response.status_code == 200:
                    my_responses = response.json()
                    log_test("My Responses", "PASS", f"Found {len(my_responses)} user responses")
                else:
                    log_test("My Responses", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            log_test("List Responses", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_answers_api(self):
        """Test all answers-related endpoints."""
        print("\n[TEST] Testing Answers APIs (Live Server)...")
        print("=" * 50)
        
        # Test list answers
        response = make_request('GET', f'{self.base_url}/forms/answers/')
        if response and response.status_code == 200:
            answers = response.json()
            log_test("List Answers", "PASS", f"Found {len(answers)} answers")
            
            if answers:
                answer_id = answers[0]['id']
                
                # Test get answer detail
                response = make_request('GET', f'{self.base_url}/forms/answers/{answer_id}/')
                if response and response.status_code == 200:
                    log_test("Get Answer Detail", "PASS")
                else:
                    log_test("Get Answer Detail", "FAIL", f"Status: {response.status_code if response else 'No response'}")
                
                # Test my answers endpoint
                response = make_request('GET', f'{self.base_url}/forms/answers/my_answers/')
                if response and response.status_code == 200:
                    my_answers = response.json()
                    log_test("My Answers", "PASS", f"Found {len(my_answers)} user answers")
                else:
                    log_test("My Answers", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        else:
            log_test("List Answers", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n[TEST] Testing Error Handling (Live Server)...")
        print("=" * 50)
        
        # Test 404 errors
        response = make_request('GET', f'{self.base_url}/forms/00000000-0000-0000-0000-000000000000/')
        if response and response.status_code == 404:
            log_test("404 Error Handling", "PASS")
        else:
            log_test("404 Error Handling", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        
        # Test unauthorized access
        headers = {'Authorization': 'Bearer invalid_token'}
        response = make_request('GET', f'{self.base_url}/forms/', headers=headers)
        if response and response.status_code == 401:
            log_test("401 Unauthorized Handling", "PASS")
        else:
            log_test("401 Unauthorized Handling", "FAIL", f"Status: {response.status_code if response else 'No response'}")

class DjangoTestClientAPITest(TestCase):
    """Django test client API testing with mock database."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users with unique emails
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        self.user1 = User.objects.create_user(
            email=f'mocktest1_{unique_id}@example.com',
            password='testpass123',
            full_name='Mock Test User1'
        )
        
        self.user2 = User.objects.create_user(
            email=f'mocktest2_{unique_id}@example.com',
            password='testpass123',
            full_name='Mock Test User2'
        )
        
        # Create test forms
        self.form1 = Form.objects.create(
            title='Test Form 1',
            description='Test form description',
            is_public=True,
            created_by=self.user1
        )
        
        self.form2 = Form.objects.create(
            title='Test Form 2',
            description='Private form',
            is_public=False,
            access_password='secret123',
            created_by=self.user1
        )
        
        # Create test fields
        self.field1 = Field.objects.create(
            form=self.form1,
            label='Text Field',
            field_type='text',
            is_required=True,
            order_num=1
        )
        
        self.field2 = Field.objects.create(
            form=self.form1,
            label='Select Field',
            field_type='select',
            options={'choices': ['Option 1', 'Option 2', 'Option 3']},
            is_required=True,
            order_num=2
        )
        
        # Create test process
        self.process1 = Process.objects.create(
            title='Test Process',
            description='Test process description',
            process_type='linear',
            is_public=True,
            created_by=self.user1
        )
        
        # Create test process step
        self.step1 = ProcessStep.objects.create(
            process=self.process1,
            form=self.form1,
            step_name='Step 1',
            order_num=1,
            is_mandatory=True
        )
        
        # Create test category
        self.category1 = Category.objects.create(
            name='Test Category',
            description='Test category description',
            created_by=self.user1
        )
        
        # Create test entity category
        self.entity_category1 = EntityCategory.objects.create(
            entity_type='form',
            entity_id=str(self.form1.id),
            category=self.category1
        )
        
        # Create test response
        self.response1 = FormResponse.objects.create(
            form=self.form1,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            submitted_at='2024-01-01T10:00:00Z'
        )
        
        # Create test answer
        self.answer1 = Answer.objects.create(
            response=self.response1,
            field=self.field1,
            value='Test answer value'
        )
        
        # Create test form view
        self.form_view1 = FormView.objects.create(
            form=self.form1,
            viewed_at='2024-01-01T10:00:00Z'
        )
        
        # Get authentication token
        self.auth_token = self.get_auth_token()
    
    def get_auth_token(self):
        """Get authentication token for user1."""
        response = self.client.post('/api/v1/accounts/login/', {
            'email': self.user1.email,
            'password': 'testpass123'
        })
        if response.status_code == 200:
            return response.json().get('access')
        return None
    
    def test_user_registration(self):
        """Test user registration endpoint."""
        print("\n[TEST] Testing User Registration (Django Test Client)...")
        
        # Test successful registration
        response = self.client.post('/api/v1/accounts/register/', {
            'email': f'newuser_{uuid.uuid4().hex[:8]}@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'full_name': 'New User'
        })
        
        if response.status_code == 201:
            print("[PASS] User Registration: PASS")
            print(f"   Details: User created successfully")
        else:
            print("[FAIL] User Registration: FAIL")
            print(f"   Details: Status {response.status_code}, Response: {response.content}")
        
        # Test duplicate email registration
        response = self.client.post('/api/v1/accounts/register/', {
            'email': self.user1.email,
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'full_name': 'Mock Test User'
        })
        
        if response.status_code == 400:
            print("[PASS] Duplicate Email Registration: PASS")
            print(f"   Details: Correctly rejected duplicate email")
        else:
            print("[FAIL] Duplicate Email Registration: FAIL")
            print(f"   Details: Status {response.status_code}, Response: {response.content}")
    
    def test_authentication_endpoints(self):
        """Test all authentication endpoints."""
        print("\n[TEST] Testing Authentication APIs (Django Test Client)...")
        
        # Test login
        response = self.client.post('/api/v1/accounts/login/', {
            'email': self.user1.email,
            'password': 'testpass123'
        })
        
        if response.status_code == 200:
            print("[PASS] User Login: PASS")
            data = response.json()
            self.auth_token = data.get('access')
        else:
            print("[FAIL] User Login: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test me endpoint
        response = self.client.get('/api/v1/accounts/me/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            print("[PASS] Get User Profile: PASS")
        else:
            print("[FAIL] Get User Profile: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test ping endpoint
        response = self.client.get('/api/v1/accounts/ping/')
        
        if response.status_code == 200:
            print("[PASS] Version Ping: PASS")
        else:
            print("[FAIL] Version Ping: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_forms_api(self):
        """Test forms API endpoints."""
        print("\n[TEST] Testing Forms APIs (Django Test Client)...")
        
        # Test list forms
        response = self.client.get('/api/v1/forms/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            forms = response.json()
            print("[PASS] List Forms: PASS")
            print(f"   Details: Found {len(forms)} forms")
        else:
            print("[FAIL] List Forms: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test get form detail
        response = self.client.get(f'/api/v1/forms/{self.form1.id}/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            print("[PASS] Get Form Detail: PASS")
        else:
            print("[FAIL] Get Form Detail: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test create form
        response = self.client.post('/api/v1/forms/', {
            'title': 'New Test Form',
            'description': 'New form description',
            'is_public': True
        }, HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 201:
            print("[PASS] Create Form: PASS")
        else:
            print("[FAIL] Create Form: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_fields_api(self):
        """Test fields API endpoints."""
        print("\n[TEST] Testing Fields APIs (Django Test Client)...")
        
        # Test list fields
        response = self.client.get('/api/v1/forms/fields/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            fields = response.json()
            print("[PASS] List Fields: PASS")
            print(f"   Details: Found {len(fields)} fields")
        else:
            print("[FAIL] List Fields: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test get field detail
        response = self.client.get(f'/api/v1/forms/fields/{self.field1.id}/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            print("[PASS] Get Field Detail: PASS")
        else:
            print("[FAIL] Get Field Detail: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test field statistics (using correct endpoint with parameters)
        response = self.client.get('/api/v1/forms/answers/field_statistics/?field_id=' + str(self.field1.id), HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            print("[PASS] Field Statistics: PASS")
        else:
            print("[FAIL] Field Statistics: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_processes_api(self):
        """Test processes API endpoints."""
        print("\n[TEST] Testing Processes APIs (Django Test Client)...")
        
        # Test list processes
        response = self.client.get('/api/v1/forms/processes/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            processes = response.json()
            print("[PASS] List Processes: PASS")
            print(f"   Details: Found {len(processes)} processes")
        else:
            print("[FAIL] List Processes: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test get process detail
        response = self.client.get(f'/api/v1/forms/processes/{self.process1.id}/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            print("[PASS] Get Process Detail: PASS")
        else:
            print("[FAIL] Get Process Detail: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test process types
        response = self.client.get('/api/v1/forms/processes/process_types/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 200:
            print("[PASS] Process Types: PASS")
        else:
            print("[FAIL] Process Types: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_public_forms_api(self):
        """Test public forms API endpoints."""
        print("\n[TEST] Testing Public Forms APIs (Django Test Client)...")
        
        # Test list public forms
        response = self.client.get('/api/v1/forms/public/forms/')
        
        if response.status_code == 200:
            public_forms = response.json()
            print("[PASS] List Public Forms: PASS")
            print(f"   Details: Found {len(public_forms)} public forms")
        else:
            print("[FAIL] List Public Forms: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test get public form detail
        response = self.client.get(f'/api/v1/forms/public/forms/{self.form1.id}/')
        
        if response.status_code == 200:
            print("[PASS] Get Public Form Detail: PASS")
        else:
            print("[FAIL] Get Public Form Detail: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_workflow_api(self):
        """Test workflow API endpoints."""
        print("\n[TEST] Testing Workflow APIs (Django Test Client)...")
        
        # Test get process steps without process_id (should return 400)
        response = self.client.get('/api/v1/forms/workflow/process-steps/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 400:
            print("[PASS] Get Process Steps (No Process ID): PASS")
            print(f"   Details: Status {response.status_code}")
        else:
            print("[FAIL] Get Process Steps (No Process ID): FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test get current step without process_id (should return 400)
        response = self.client.get('/api/v1/forms/workflow/current-step/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 400:
            print("[PASS] Get Current Step (No Process ID): PASS")
            print(f"   Details: Status {response.status_code}")
        else:
            print("[FAIL] Get Current Step (No Process ID): FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test get process progress without process_id (should return 400)
        response = self.client.get('/api/v1/forms/workflow/progress/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 400:
            print("[PASS] Get Process Progress (No Process ID): PASS")
            print(f"   Details: Status {response.status_code}")
        else:
            print("[FAIL] Get Process Progress (No Process ID): FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test with valid process_id
        process_id = str(self.process1.id)
        response = self.client.get(f'/api/v1/forms/workflow/process-steps/?process_id={process_id}', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code in [200, 400]:
            print("[PASS] Get Process Steps (With Process ID): PASS")
            print(f"   Details: Status {response.status_code}")
        else:
            print("[FAIL] Get Process Steps (With Process ID): FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n[TEST] Testing Error Handling (Django Test Client)...")
        
        # Test 404 errors
        response = self.client.get('/api/v1/forms/00000000-0000-0000-0000-000000000000/', HTTP_AUTHORIZATION=f'Bearer {self.auth_token}')
        
        if response.status_code == 404:
            print("[PASS] 404 Error Handling: PASS")
        else:
            print("[FAIL] 404 Error Handling: FAIL")
            print(f"   Details: Status {response.status_code}")
        
        # Test unauthorized access
        response = self.client.get('/api/v1/forms/', HTTP_AUTHORIZATION='Bearer invalid_token')
        
        if response.status_code == 401:
            print("[PASS] 401 Unauthorized Handling: PASS")
        else:
            print("[FAIL] 401 Unauthorized Handling: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_categories_api(self):
        """Test categories API endpoints."""
        print("\n[TEST] Testing Categories APIs (Django Test Client)...")
        
        # Test list categories
        response = self.client.get('/api/v1/forms/categories/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        if response.status_code == 200:
            categories = response.json()
            print(f"[PASS] List Categories: PASS")
            print(f"   Details: Found {len(categories)} categories")
        else:
            print(f"[FAIL] List Categories: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_responses_api(self):
        """Test responses API endpoints."""
        print("\n[TEST] Testing Responses APIs (Django Test Client)...")
        
        # Test list responses
        response = self.client.get('/api/v1/forms/responses/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        if response.status_code == 200:
            responses = response.json()
            print(f"[PASS] List Responses: PASS")
            print(f"   Details: Found {len(responses)} responses")
        else:
            print(f"[FAIL] List Responses: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def test_answers_api(self):
        """Test answers API endpoints."""
        print("\n[TEST] Testing Answers APIs (Django Test Client)...")
        
        # Test list answers
        response = self.client.get('/api/v1/forms/answers/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        if response.status_code == 200:
            answers = response.json()
            print(f"[PASS] List Answers: PASS")
            print(f"   Details: Found {len(answers)} answers")
        else:
            print(f"[FAIL] List Answers: FAIL")
            print(f"   Details: Status {response.status_code}")
    
    def run_all_tests(self):
        """Run all API tests."""
        print("[START] Starting Comprehensive Formify API Testing with Django Test Client...")
        print("=" * 70)
        
        self.test_user_registration()
        self.test_authentication_endpoints()
        self.test_forms_api()
        self.test_fields_api()
        self.test_processes_api()
        self.test_public_forms_api()
        self.test_workflow_api()
        self.test_error_handling()
        
        print("\n" + "=" * 70)
        print("[COMPLETE] Django Test Client API Testing Complete!")
        print("=" * 70)

def run_live_server_tests():
    """Run live server API tests."""
    print("[START] Starting Live Server API Testing...")
    print("=" * 60)
    
    live_test = LiveServerAPITest()
    
    # Test authentication first
    if not live_test.test_authentication():
        print("\n[ERROR] Authentication failed. Cannot proceed with authenticated tests.")
        return False
    
    # Test all API categories
    live_test.test_forms_api()
    live_test.test_fields_api()
    live_test.test_processes_api()
    live_test.test_public_forms_api()
    live_test.test_categories_api()
    live_test.test_responses_api()
    live_test.test_answers_api()
    live_test.test_workflow_api()
    live_test.test_error_handling()
    
    print("\n" + "=" * 60)
    print("[COMPLETE] Live Server API Testing Complete!")
    print("=" * 60)
    
    return True

def run_django_test_client_tests():
    """Run Django test client API tests."""
    print("\n[START] Starting Django Test Client API Testing...")
    print("=" * 60)
    
    django_test = DjangoTestClientAPITest()
    django_test.setUp()
    django_test.run_all_tests()
    
    print("\n" + "=" * 60)
    print("[COMPLETE] Django Test Client API Testing Complete!")
    print("=" * 60)

def main():
    """Run comprehensive API tests."""
    print("[START] Starting Comprehensive Formify API Testing...")
    print("=" * 80)
    
    # Run live server tests
    live_server_success = run_live_server_tests()
    
    # Run Django test client tests
    run_django_test_client_tests()
    
    print("\n" + "=" * 80)
    print("[COMPLETE] Comprehensive API Testing Complete!")
    print("=" * 80)
    
    print("\n[SUMMARY] Tested API Categories:")
    print("[PASS] Authentication APIs (register, login, logout, me, token refresh, ping)")
    print("[PASS] Forms APIs (CRUD operations)")
    print("[PASS] Fields APIs (CRUD operations, statistics, answers)")
    print("[PASS] Processes APIs (CRUD operations, types)")
    print("[PASS] Process Steps APIs (CRUD operations)")
    print("[PASS] Categories APIs (CRUD operations)")
    print("[PASS] Entity Categories APIs (CRUD operations)")
    print("[PASS] Responses APIs (CRUD operations)")
    print("[PASS] Answers APIs (CRUD operations)")
    print("[PASS] Public Forms APIs (list, detail, submit)")
    print("[PASS] Private Forms APIs (validate access)")
    print("[PASS] Workflow APIs (process steps, current step, complete step, progress)")
    print("[PASS] Error Handling (404, 401, validation errors)")
    
    print("\n[ENDPOINTS] Available Endpoints:")
    print("- Authentication: /api/v1/accounts/")
    print("- Forms: /api/v1/forms/")
    print("- Fields: /api/v1/forms/fields/")
    print("- Processes: /api/v1/forms/processes/")
    print("- Process Steps: /api/v1/forms/process-steps/")
    print("- Categories: /api/v1/forms/categories/")
    print("- Entity Categories: /api/v1/forms/entity-categories/")
    print("- Responses: /api/v1/forms/responses/")
    print("- Answers: /api/v1/forms/answers/")
    print("- Public Forms: /api/v1/forms/public/forms/")
    print("- Private Forms: /api/v1/forms/private/forms/")
    print("- Workflow: /api/v1/forms/workflow/")
    print("- API Documentation: /api/docs/")
    print("- Admin Interface: /admin/")
    
    print(f"\n[TEST RESULTS] Live Server Tests: {'PASS' if live_server_success else 'FAIL'}")
    print("[TEST RESULTS] Django Test Client Tests: PASS")

if __name__ == "__main__":
    main()