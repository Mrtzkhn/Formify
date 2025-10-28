#!/usr/bin/env python
"""
API Testing Script for Formify
This script demonstrates how to use the APIs with the seeded data.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

def test_authentication():
    """Test user authentication and get JWT token."""
    print("Testing Authentication...")
    
    # Try login with existing test user
    login_data = {
        "email": "test1@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/accounts/login/", json=login_data)
    if response.status_code == 200:
        print("User login successful")
        token_data = response.json()
        return token_data['access']
    else:
        print(f"Login failed: {response.status_code}")
        return None

def test_forms_api(token: str):
    """Test forms API endpoints."""
    print("\nTesting Forms API...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List forms
    response = requests.get(f"{BASE_URL}/forms/forms/", headers=headers)
    if response.status_code == 200:
        forms = response.json()
        print(f"Found {len(forms)} forms")
        
        if forms:
            form_id = forms[0]['id']
            print(f"Testing with form: {forms[0]['title']}")
            
            # Get form details
            response = requests.get(f"{BASE_URL}/forms/forms/{form_id}/", headers=headers)
            if response.status_code == 200:
                print("Form details retrieved")
            
            # Get form fields
            response = requests.get(f"{BASE_URL}/forms/fields/?form_id={form_id}", headers=headers)
            if response.status_code == 200:
                fields = response.json()
                print(f"Found {len(fields)} fields for form")
    else:
        print(f"Forms API failed: {response.status_code}")

def test_public_forms_api():
    """Test public forms API."""
    print("\nTesting Public Forms API...")
    
    # List public forms
    response = requests.get(f"{BASE_URL}/forms/public/forms/")
    if response.status_code == 200:
        forms = response.json()
        print(f"Found {len(forms)} public forms")
        
        if forms:
            form_id = forms[0]['id']
            print(f"Testing public form: {forms[0]['title']}")
            
            # Get public form details
            response = requests.get(f"{BASE_URL}/forms/public/forms/{form_id}/")
            if response.status_code == 200:
                print("Public form details retrieved")
                
                # Test form submission
                form_data = response.json()
                fields = form_data.get('fields', [])
                
                if fields:
                    answers = []
                    for field in fields:
                        if field['field_type'] == 'select':
                            choices = field['options'].get('choices', [])
                            value = choices[0] if choices else 'Test'
                        elif field['field_type'] == 'checkbox':
                            choices = field['options'].get('choices', [])
                            value = choices[0] if choices else 'Yes'
                        else:  # text
                            value = f"Test answer for {field['label']}"
                        
                        answers.append({
                            "field_id": field['id'],
                            "value": value
                        })
                    
                    submission_data = {"answers": answers}
                    response = requests.post(
                        f"{BASE_URL}/forms/public/forms/{form_id}/submit/",
                        json=submission_data
                    )
                    if response.status_code == 201:
                        print("Form submission successful")
                    else:
                        print(f"Form submission failed: {response.status_code}")
                        print(response.text)
    else:
        print(f"Public forms API failed: {response.status_code}")

def test_processes_api(token: str):
    """Test processes API endpoints."""
    print("\nTesting Processes API...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List processes
    response = requests.get(f"{BASE_URL}/forms/processes/", headers=headers)
    if response.status_code == 200:
        processes = response.json()
        print(f"Found {len(processes)} processes")
        
        if processes:
            process_id = processes[0]['id']
            print(f"Testing with process: {processes[0]['title']}")
            
            # Get process steps
            response = requests.get(f"{BASE_URL}/forms/workflow/process-steps/?process_id={process_id}", headers=headers)
            if response.status_code == 200:
                steps = response.json()
                print(f"Found {len(steps)} process steps")
    else:
        print(f"Processes API failed: {response.status_code}")

def test_categories_api(token: str):
    """Test categories API endpoints."""
    print("\nTesting Categories API...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List categories
    response = requests.get(f"{BASE_URL}/forms/categories/", headers=headers)
    if response.status_code == 200:
        categories = response.json()
        print(f"Found {len(categories)} categories")
        
        if categories:
            category_id = categories[0]['id']
            print(f"Testing with category: {categories[0]['name']}")
            
            # Get entities by category
            response = requests.get(f"{BASE_URL}/forms/entity-categories/by_entity/?entity_type=form", headers=headers)
            if response.status_code == 200:
                entities = response.json()
                print(f"Found {len(entities)} entity categories")
    else:
        print(f"Categories API failed: {response.status_code}")

def main():
    """Main testing function."""
    print("Starting Formify API Testing...")
    print("=" * 50)
    
    try:
        # Test authentication
        token = test_authentication()
        if not token:
            print("Authentication failed, skipping authenticated tests")
            return
        
        # Test various API endpoints
        test_forms_api(token)
        test_public_forms_api()
        test_processes_api(token)
        test_categories_api(token)
        
        print("\n" + "=" * 50)
        print("API Testing Complete!")
        print("\nAvailable API Endpoints:")
        print("- Authentication: /api/v1/accounts/")
        print("- Forms: /api/v1/forms/forms/")
        print("- Fields: /api/v1/forms/fields/")
        print("- Processes: /api/v1/forms/processes/")
        print("- Categories: /api/v1/forms/categories/")
        print("- Public Forms: /api/v1/forms/public/forms/")
        print("- API Documentation: /api/docs/")
        print("- Admin Interface: /admin/")
        
    except requests.exceptions.ConnectionError:
        print("Connection failed. Make sure the Django server is running:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()