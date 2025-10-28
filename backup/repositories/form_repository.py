from typing import List
from django.db import transaction
from forms.models import Form, FormView
from .base_repository import BaseRepository


class FormRepository(BaseRepository):
    """Repository for Form model operations."""
    
    def __init__(self):
        super().__init__(Form)
    
    def get_by_user(self, user_id: str) -> List[Form]:
        """Get all forms for a specific user."""
        return list(Form.objects.filter(created_by_id=user_id).order_by('-created_at'))
    
    def get_public_forms(self) -> List[Form]:
        """Get all public and active forms."""
        return list(Form.objects.filter(
            is_public=True, 
            is_active=True
        ).order_by('-created_at'))
    
    def get_by_id_with_access_check(self, form_id: str, user=None) -> Form:
        """Get form by ID with access control."""
        try:
            form = Form.objects.get(id=form_id, is_active=True)
            
            # If form is public, anyone can access it
            if form.is_public:
                return form
            
            # If form is private, only the creator can access it
            if user and form.created_by == user:
                return form
            
            # Private form, no access
            return None
        except Form.DoesNotExist:
            return None
    
    def get_public_form_by_id(self, form_id: str) -> Form:
        """Get a public form by ID."""
        try:
            return Form.objects.get(
                id=form_id, 
                is_public=True, 
                is_active=True
            )
        except Form.DoesNotExist:
            return None
    
    def validate_password(self, form_id: str, password: str) -> bool:
        """Validate access password for a private form."""
        try:
            form = Form.objects.get(id=form_id, is_active=True)
            return form.access_password == password
        except Form.DoesNotExist:
            return False
    
    def track_view(self, form: Form, ip_address: str, user_agent: str) -> FormView:
        """Track a form view."""
        return FormView.objects.create(
            form=form,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_form_with_fields(self, form_id: str) -> Form:
        """Get form with its fields."""
        try:
            return Form.objects.prefetch_related('fields').get(id=form_id)
        except Form.DoesNotExist:
            return None
