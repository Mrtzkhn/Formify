from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from forms.models import (
    Form, Field, Process, ProcessStep, Category, EntityCategory, 
    Response as FormResponse, Answer, FormView
)
import json
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Creating sample data...')
        
        with transaction.atomic():
            # Create users
            users = self.create_users()
            
            # Create categories
            categories = self.create_categories(users)
            
            # Create forms with fields
            forms = self.create_forms_with_fields(users)
            
            # Create processes with steps
            processes = self.create_processes_with_steps(users, forms)
            
            # Create entity categories
            self.create_entity_categories(forms, processes, categories)
            
            # Create responses and answers
            self.create_responses_and_answers(forms, users)
            
            # Create form views
            self.create_form_views(forms, users)

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with sample data!')
        )

    def clear_data(self):
        """Clear existing data."""
        FormView.objects.all().delete()
        Answer.objects.all().delete()
        FormResponse.objects.all().delete()
        EntityCategory.objects.all().delete()
        ProcessStep.objects.all().delete()
        Process.objects.all().delete()
        Field.objects.all().delete()
        Form.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(email__startswith='test').delete()

    def create_users(self):
        """Create sample users."""
        users = []
        
        # Create test users
        test_users_data = [
            {
                'email': 'test1@example.com',
                'full_name': 'Test User 1',
                'phone_number': '+1234567890'
            },
            {
                'email': 'test2@example.com',
                'full_name': 'Test User 2',
                'phone_number': '+1234567891'
            },
            {
                'email': 'test3@example.com',
                'full_name': 'Test User 3',
                'phone_number': '+1234567892'
            },
            {
                'email': 'admin@example.com',
                'full_name': 'Admin User',
                'phone_number': '+1234567893',
                'is_staff': True,
                'is_superuser': True
            }
        ]
        
        for user_data in test_users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'full_name': user_data['full_name'],
                    'phone_number': user_data.get('phone_number', ''),
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False)
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
            
        self.stdout.write(f'Created {len(users)} users')
        return users

    def create_categories(self, users):
        """Create sample categories."""
        categories = []
        
        category_data = [
            {
                'name': 'Customer Feedback',
                'description': 'Forms and processes related to customer feedback collection',
                'created_by': users[0]
            },
            {
                'name': 'Employee Surveys',
                'description': 'Internal surveys and feedback forms for employees',
                'created_by': users[1]
            },
            {
                'name': 'Product Research',
                'description': 'Research forms and processes for product development',
                'created_by': users[0]
            },
            {
                'name': 'Event Management',
                'description': 'Forms and processes for managing events and registrations',
                'created_by': users[2]
            }
        ]
        
        for cat_data in category_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                created_by=cat_data['created_by'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            
        self.stdout.write(f'Created {len(categories)} categories')
        return categories

    def create_forms_with_fields(self, users):
        """Create sample forms with fields."""
        forms = []
        
        # Form 1: Customer Feedback Form
        form1, created = Form.objects.get_or_create(
            title='Customer Feedback Form',
            created_by=users[0],
            defaults={
                'description': 'Collect feedback from customers about our products and services',
                'is_public': True,
                'is_active': True
            }
        )
        forms.append(form1)
        
        if created:
            # Add fields to form1
            fields_data = [
                {
                    'label': 'Overall Satisfaction',
                    'field_type': 'select',
                    'is_required': True,
                    'order_num': 1,
                    'options': {'choices': ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied', 'Very Dissatisfied']}
                },
                {
                    'label': 'Product Quality Rating',
                    'field_type': 'select',
                    'is_required': True,
                    'order_num': 2,
                    'options': {'choices': ['Excellent', 'Good', 'Average', 'Poor', 'Very Poor']}
                },
                {
                    'label': 'Comments',
                    'field_type': 'text',
                    'is_required': False,
                    'order_num': 3,
                    'options': {}
                },
                {
                    'label': 'Would you recommend us?',
                    'field_type': 'checkbox',
                    'is_required': True,
                    'order_num': 4,
                    'options': {'choices': ['Yes', 'No']}
                }
            ]
            
            for field_data in fields_data:
                Field.objects.create(form=form1, **field_data)
        
        # Form 2: Employee Survey
        form2, created = Form.objects.get_or_create(
            title='Employee Satisfaction Survey',
            created_by=users[1],
            defaults={
                'description': 'Internal survey to measure employee satisfaction and engagement',
                'is_public': False,
                'access_password': 'employee2024',
                'is_active': True
            }
        )
        forms.append(form2)
        
        if created:
            fields_data = [
                {
                    'label': 'Job Satisfaction',
                    'field_type': 'select',
                    'is_required': True,
                    'order_num': 1,
                    'options': {'choices': ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied', 'Very Dissatisfied']}
                },
                {
                    'label': 'Work-Life Balance',
                    'field_type': 'select',
                    'is_required': True,
                    'order_num': 2,
                    'options': {'choices': ['Excellent', 'Good', 'Average', 'Poor', 'Very Poor']}
                },
                {
                    'label': 'Management Support',
                    'field_type': 'select',
                    'is_required': True,
                    'order_num': 3,
                    'options': {'choices': ['Strongly Agree', 'Agree', 'Neutral', 'Disagree', 'Strongly Disagree']}
                },
                {
                    'label': 'Additional Comments',
                    'field_type': 'text',
                    'is_required': False,
                    'order_num': 4,
                    'options': {}
                }
            ]
            
            for field_data in fields_data:
                Field.objects.create(form=form2, **field_data)
        
        # Form 3: Product Research Form
        form3, created = Form.objects.get_or_create(
            title='Product Feature Request',
            created_by=users[0],
            defaults={
                'description': 'Collect feature requests and product improvement suggestions',
                'is_public': True,
                'is_active': True
            }
        )
        forms.append(form3)
        
        if created:
            fields_data = [
                {
                    'label': 'Feature Category',
                    'field_type': 'select',
                    'is_required': True,
                    'order_num': 1,
                    'options': {'choices': ['User Interface', 'Performance', 'Security', 'Integration', 'Other']}
                },
                {
                    'label': 'Feature Description',
                    'field_type': 'text',
                    'is_required': True,
                    'order_num': 2,
                    'options': {}
                },
                {
                    'label': 'Priority Level',
                    'field_type': 'select',
                    'is_required': True,
                    'order_num': 3,
                    'options': {'choices': ['High', 'Medium', 'Low']}
                },
                {
                    'label': 'Contact for Follow-up',
                    'field_type': 'checkbox',
                    'is_required': False,
                    'order_num': 4,
                    'options': {'choices': ['Yes', 'No']}
                }
            ]
            
            for field_data in fields_data:
                Field.objects.create(form=form3, **field_data)
        
        self.stdout.write(f'Created {len(forms)} forms with fields')
        return forms

    def create_processes_with_steps(self, users, forms):
        """Create sample processes with steps."""
        processes = []
        
        # Process 1: Customer Onboarding
        process1, created = Process.objects.get_or_create(
            title='Customer Onboarding Process',
            created_by=users[0],
            defaults={
                'description': 'Complete onboarding process for new customers',
                'process_type': 'linear',
                'is_public': True,
                'is_active': True
            }
        )
        processes.append(process1)
        
        if created:
            steps_data = [
                {
                    'step_name': 'Account Setup',
                    'step_description': 'Complete account registration and verification',
                    'form': forms[0],  # Customer Feedback Form
                    'order_num': 1,
                    'is_required': True,
                    'is_mandatory': True
                },
                {
                    'step_name': 'Profile Completion',
                    'step_description': 'Fill out detailed profile information',
                    'form': forms[2],  # Product Research Form
                    'order_num': 2,
                    'is_required': True,
                    'is_mandatory': True
                }
            ]
            
            for step_data in steps_data:
                ProcessStep.objects.create(process=process1, **step_data)
        
        # Process 2: Employee Evaluation
        process2, created = Process.objects.get_or_create(
            title='Employee Performance Evaluation',
            created_by=users[1],
            defaults={
                'description': 'Annual employee performance evaluation process',
                'process_type': 'free',
                'is_public': False,
                'access_password': 'eval2024',
                'is_active': True
            }
        )
        processes.append(process2)
        
        if created:
            steps_data = [
                {
                    'step_name': 'Self Assessment',
                    'step_description': 'Employee self-evaluation form',
                    'form': forms[1],  # Employee Survey
                    'order_num': 1,
                    'is_required': True,
                    'is_mandatory': True
                },
                {
                    'step_name': 'Manager Review',
                    'step_description': 'Manager evaluation and feedback',
                    'form': forms[0],  # Customer Feedback Form (reused)
                    'order_num': 2,
                    'is_required': True,
                    'is_mandatory': False
                }
            ]
            
            for step_data in steps_data:
                ProcessStep.objects.create(process=process2, **step_data)
        
        self.stdout.write(f'Created {len(processes)} processes with steps')
        return processes

    def create_entity_categories(self, forms, processes, categories):
        """Create entity category associations."""
        associations = []
        
        # Associate forms with categories
        form_category_mapping = [
            (forms[0], categories[0]),  # Customer Feedback Form -> Customer Feedback
            (forms[1], categories[1]),  # Employee Survey -> Employee Surveys
            (forms[2], categories[2]),  # Product Research Form -> Product Research
        ]
        
        for form, category in form_category_mapping:
            association, created = EntityCategory.objects.get_or_create(
                entity_type='form',
                entity_id=str(form.id),
                category=category
            )
            associations.append(association)
        
        # Associate processes with categories
        process_category_mapping = [
            (processes[0], categories[0]),  # Customer Onboarding -> Customer Feedback
            (processes[1], categories[1]),  # Employee Evaluation -> Employee Surveys
        ]
        
        for process, category in process_category_mapping:
            association, created = EntityCategory.objects.get_or_create(
                entity_type='process',
                entity_id=str(process.id),
                category=category
            )
            associations.append(association)
        
        self.stdout.write(f'Created {len(associations)} entity category associations')

    def create_responses_and_answers(self, forms, users):
        """Create sample responses and answers."""
        responses = []
        
        # Create responses for each form
        for form in forms:
            for i in range(3):  # 3 responses per form
                response = FormResponse.objects.create(
                    form=form,
                    submitted_by=users[i % len(users)],
                    ip_address=f'192.168.1.{i+10}',
                    user_agent=f'Mozilla/5.0 (Test Browser {i+1})'
                )
                responses.append(response)
                
                # Create answers for each field
                for field in form.fields.all():
                    if field.field_type == 'select':
                        value = field.options.get('choices', ['Option 1'])[i % len(field.options.get('choices', ['Option 1']))]
                    elif field.field_type == 'checkbox':
                        value = field.options.get('choices', ['Yes'])[i % len(field.options.get('choices', ['Yes']))]
                    else:  # text
                        value = f'Sample answer {i+1} for {field.label}'
                    
                    Answer.objects.create(
                        response=response,
                        field=field,
                        value=value
                    )
        
        self.stdout.write(f'Created {len(responses)} responses with answers')

    def create_form_views(self, forms, users):
        """Create sample form views."""
        views = []
        
        for form in forms:
            for i in range(5):  # 5 views per form
                view = FormView.objects.create(
                    form=form,
                    ip_address=f'192.168.1.{i+20}',
                    user_agent=f'Mozilla/5.0 (Viewer Browser {i+1})'
                )
                views.append(view)
        
        self.stdout.write(f'Created {len(views)} form views')
