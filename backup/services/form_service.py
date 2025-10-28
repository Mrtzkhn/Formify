from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from forms.models import Form, FormView
from forms.repositories.form_repository import FormRepository
from typing import Dict, List, Any


class FormService:
    """Service layer for form operations with business logic."""
    
    def __init__(self):
        self.form_repository = FormRepository()
    
    def create_form(self, user, form_data: Dict[str, Any]) -> Form:
        """
        Create a new form.
        
        Args:
            user: The authenticated user
            form_data: Dictionary containing form data
            
        Returns:
            Form: The created form instance
            
        Raises:
            ValidationError: If form data is invalid
        """
        # Validate access password for private forms
        is_public = form_data.get('is_public', True)
        access_password = form_data.get('access_password', '')
        
        if not is_public and not access_password:
            raise ValidationError("Private forms require an access password.")
        
        # Create the form
        form = self.form_repository.create(
            created_by=user,
            **form_data
        )
        
        return form
    
    def get_user_forms(self, user) -> List[Form]:
        """
        Get all forms for user.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[Form]: List of forms belonging to user
        """
        return self.form_repository.get_by_user(str(user.id))
    
    def get_public_forms(self) -> List[Form]:
        """
        Get all public forms.
        
        Returns:
            List[Form]: List of public forms
        """
        return self.form_repository.get_public_forms()
    
    def get_form(self, user, form_id: str) -> Form:
        """
        Get a specific form by ID.
        
        Args:
            user: The authenticated user
            form_id: UUID of the form
            
        Returns:
            Form: The form instance
            
        Raises:
            PermissionDenied: If user doesn't own the form
        """
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return form
    
    def update_form(self, user, form_id: str, form_data: Dict[str, Any]) -> Form:
        """
        Update an existing form.
        
        Args:
            user: The authenticated user
            form_id: UUID of the form
            form_data: Dictionary containing updated form data
            
        Returns:
            Form: The updated form instance
            
        Raises:
            PermissionDenied: If user doesn't own the form
            ValidationError: If form data is invalid
        """
        form = get_object_or_404(Form, id=form_id, created_by=user)
        
        # Validate access password for private forms
        is_public = form_data.get('is_public', form.is_public)
        access_password = form_data.get('access_password', form.access_password)
        
        if not is_public and not access_password:
            raise ValidationError("Private forms require an access password.")
        
        # Update the form using repository
        return self.form_repository.update(form, **form_data)
    
    def delete_form(self, user, form_id: str) -> bool:
        """
        Delete a form.
        
        Args:
            user: The authenticated user
            form_id: UUID of the form
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            PermissionDenied: If user doesn't own the form
        """
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return self.form_repository.delete(form)
    
    def get_public_form(self, form_id: str) -> Form:
        """
        Get a public form by ID.
        
        Args:
            form_id: UUID of the form
            
        Returns:
            Form: The public form instance or None if not found/not public
        """
        return self.form_repository.get_public_form_by_id(form_id)
    
    def validate_form_access(self, form_id: str, password: str = None) -> Form:
        """
        Validate access to a form (public or with password).
        
        Args:
            form_id: UUID of the form
            password: Access password for private forms
            
        Returns:
            Form: The form instance if access is granted
            
        Raises:
            ValidationError: If access is denied
        """
        try:
            form = Form.objects.get(id=form_id, is_active=True)
        except Form.DoesNotExist:
            raise ValidationError("Form not found or inactive.")
        
        # If form is public, allow access
        if form.is_public:
            return form
        
        # If form is private, validate password
        if not password:
            raise ValidationError("This form requires a password.")
        
        if not self.form_repository.validate_password(form_id, password):
            raise ValidationError("Invalid password.")
        
        return form
    
    def track_form_view(self, form: Form, ip_address: str, user_agent: str) -> FormView:
        """
        Track a form view.
        
        Args:
            form: The form instance
            ip_address: IP address of the viewer
            user_agent: User agent string
            
        Returns:
            FormView: The created view instance
        """
        return self.form_repository.track_view(form, ip_address, user_agent)
    
    def get_form_with_fields(self, form_id: str) -> Form:
        """
        Get form with its fields.
        
        Args:
            form_id: UUID of the form
            
        Returns:
            Form: The form instance with prefetched fields
        """
        return self.form_repository.get_form_with_fields(form_id)
