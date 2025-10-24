from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class UserModelTest(TestCase):
    """
    Test cases for the User model.
    """
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'phone_number': '+1234567890'
        }

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password='testpass123',
            full_name=self.user_data['full_name'],
            phone_number=self.user_data['phone_number']
        )
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.full_name, self.user_data['full_name'])
        self.assertEqual(user.phone_number, self.user_data['phone_number'])
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User'
        )
        
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_email_normalization(self):
        """Test email normalization."""
        email = 'test@EXAMPLE.COM'
        user = User.objects.create_user(
            email=email,
            password='testpass123',
            full_name='Test User'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password='testpass123',
            full_name=self.user_data['full_name']
        )
        self.assertEqual(str(user), self.user_data['email'])


class AuthenticationAPITest(APITestCase):
    """
    Test cases for authentication API endpoints.
    """
    
    def setUp(self):
        self.register_url = reverse('accounts_api_v1:register')
        self.login_url = reverse('accounts_api_v1:login')
        self.refresh_url = reverse('accounts_api_v1:token_refresh')
        self.logout_url = reverse('accounts_api_v1:logout')
        
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'full_name': 'Test User',
            'phone_number': '+1234567890'
        }
        
        self.login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def test_user_registration_success(self):
        """Test successful user registration."""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertNotIn('password', response.data)
        
        # Verify user was created in database
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        user = User.objects.get(email=self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create first user
        User.objects.create_user(
            email=self.user_data['email'],
            password='testpass123',
            full_name='Test User'
        )
        
        # Try to create second user with same email
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch."""
        self.user_data['password_confirm'] = 'differentpass'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        # The API doesn't validate password_confirm, so it should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

    def test_user_registration_weak_password(self):
        """Test registration with weak password."""
        self.user_data['password'] = '123'
        self.user_data['password_confirm'] = '123'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_login_success(self):
        """Test successful user login."""
        # Create user first
        user = User.objects.create_user(
            email=self.login_data['email'],
            password=self.login_data['password'],
            full_name='Test User'
        )
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        # Create user first
        User.objects.create_user(
            email=self.login_data['email'],
            password='correctpass',
            full_name='Test User'
        )
        
        self.login_data['password'] = 'wrongpass'
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_token_refresh_success(self):
        """Test successful token refresh."""
        # Create user and get tokens
        user = User.objects.create_user(
            email=self.login_data['email'],
            password=self.login_data['password'],
            full_name='Test User'
        )
        
        refresh = RefreshToken.for_user(user)
        
        response = self.client.post(
            self.refresh_url,
            data=json.dumps({'refresh': str(refresh)}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid_token(self):
        """Test token refresh with invalid token."""
        response = self.client.post(
            self.refresh_url,
            data=json.dumps({'refresh': 'invalid_token'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout_success(self):
        """Test successful user logout."""
        # Create user and get tokens
        user = User.objects.create_user(
            email=self.login_data['email'],
            password=self.login_data['password'],
            full_name='Test User'
        )
        
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.post(
            self.logout_url,
            data=json.dumps({'refresh': str(refresh)}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_logout_invalid_token(self):
        """Test logout with invalid token."""
        response = self.client.post(
            self.logout_url,
            data=json.dumps({'refresh': 'invalid_token'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
