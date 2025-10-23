from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from forms.models import Field, Form
from forms.repositories.field_repository import FieldRepository
from typing import Dict, List, Any


class FieldService:
    """Service layer for field operations with business logic."""
    
    def __init__(self):
        self.field_repository = FieldRepository()
    
    def create_field(self, user, form_id: str, field_data: Dict[str, Any]) -> Field:
        """
        Create a new field for a form.
        
        Args:
            user: The authenticated user
            form_id: UUID of the form
            field_data: Dictionary containing field data
            
        Returns:
            Field: The created field instance
            
        Raises:
            PermissionDenied: If user doesn't own the form
            ValidationError: If field data is invalid
        """
        # Verify user owns the form
        form = get_object_or_404(Form, id=form_id, created_by=user)
        
        # Set default order number if not provided
        if 'order_num' not in field_data:
            max_order = self.field_repository.get_max_order_for_form(str(form.id))
            field_data['order_num'] = max_order + 1
        
        # Validate field options
        field_type = field_data.get('field_type')
        if field_type:
            self.validate_field_options(
                field_type, 
                field_data.get('options', {})
            )
        
        # Create the field
        field = self.field_repository.create(
            form=form,
            **field_data
        )
        
        return field
    
    def get_user_fields(self, user) -> List[Field]:
        """
        Get all fields for user's forms.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[Field]: List of fields belonging to user's forms
        """
        return self.field_repository.get_by_user(str(user.id))
    
    def get_form_fields(self, user, form_id: str) -> List[Field]:
        """
        Get all fields for a specific form.
        
        Args:
            user: The authenticated user
            form_id: UUID of the form
            
        Returns:
            List[Field]: List of fields for the form
            
        Raises:
            PermissionDenied: If user doesn't own the form
        """
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return self.field_repository.get_by_form(str(form.id))
    
    def update_field(self, user, field_id: str, field_data: Dict[str, Any]) -> Field:
        """
        Update an existing field.
        
        Args:
            user: The authenticated user
            field_id: UUID of the field
            field_data: Dictionary containing updated field data
            
        Returns:
            Field: The updated field instance
            
        Raises:
            PermissionDenied: If user doesn't own the field
            ValidationError: If field data is invalid
        """
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        
        # Validate field options if field_type or options are being updated
        if 'field_type' in field_data or 'options' in field_data:
            field_type = field_data.get('field_type', field.field_type)
            options = field_data.get('options', field.options)
            self.validate_field_options(field_type, options)
        
        # Update the field using repository
        return self.field_repository.update(field, **field_data)
    
    def delete_field(self, user, field_id: str) -> bool:
        """
        Delete a field.
        
        Args:
            user: The authenticated user
            field_id: UUID of the field
            
        Returns:
            bool: True if field was deleted
            
        Raises:
            PermissionDenied: If user doesn't own the field
        """
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        
        # Store the order number before deletion
        deleted_order = field.order_num
        form_id = str(field.form.id)
        
        # Delete the field
        self.field_repository.delete(field)
        
        # Reorder remaining fields using repository
        self.field_repository.reorder_fields_after_delete(form_id, deleted_order)
        
        return True
    
    def reorder_field(self, user, field_id: str, new_order: int) -> Field:
        """
        Reorder a field within its form.
        
        Args:
            user: The authenticated user
            field_id: UUID of the field
            new_order: New order number for the field
            
        Returns:
            Field: The updated field instance
            
        Raises:
            PermissionDenied: If user doesn't own the field
            ValidationError: If new_order is invalid
        """
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        
        if new_order < 1:
            raise ValidationError("Order number must be at least 1.")
        
        max_order = self.field_repository.get_field_count_for_form(str(field.form.id))
        if new_order > max_order:
            raise ValidationError(f"Order number cannot exceed {max_order}.")
        
        old_order = field.order_num
        
        if new_order == old_order:
            return field
        
        # Use repository to handle reordering
        self.field_repository.reorder_fields_for_move(
            str(field.form.id), 
            old_order, 
            new_order, 
            str(field.id)
        )
        
        # Refresh and return the field
        field.refresh_from_db()
        return field
    
    def validate_field_options(self, field_type: str, options: Dict[str, Any]) -> bool:
        """
        Validate field options based on field type.
        
        Args:
            field_type: Type of the field
            options: Dictionary containing field options
            
        Returns:
            bool: True if options are valid
            
        Raises:
            ValidationError: If options are invalid for the field type
        """
        if field_type in ['select', 'radio', 'checkbox', 'multiselect']:
            choices = options.get('choices', [])
            if not choices:
                raise ValidationError(f"Field type '{field_type}' requires choices in options.")
            
            # Validate choices format
            for choice in choices:
                if not isinstance(choice, dict) or 'value' not in choice or 'label' not in choice:
                    raise ValidationError("Each choice must have 'value' and 'label' keys.")
        
        elif field_type == 'rating':
            min_val = options.get('min_value', 1)
            max_val = options.get('max_value', 5)
            step = options.get('step', 1)
            
            if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                raise ValidationError("Rating min_value and max_value must be numbers.")
            
            if min_val >= max_val:
                raise ValidationError("Rating min_value must be less than max_value.")
            
            if step <= 0:
                raise ValidationError("Rating step must be greater than 0.")
        
        elif field_type == 'file':
            allowed_types = options.get('allowed_types', [])
            max_size = options.get('max_size')
            
            if not allowed_types:
                raise ValidationError("File field requires allowed_types in options.")
            
            if not isinstance(allowed_types, list):
                raise ValidationError("allowed_types must be a list.")
            
            if max_size is not None and (not isinstance(max_size, (int, float)) or max_size <= 0):
                raise ValidationError("max_size must be a positive number.")
        
        elif field_type == 'number':
            min_val = options.get('min_value')
            max_val = options.get('max_value')
            step = options.get('step')
            
            if min_val is not None and not isinstance(min_val, (int, float)):
                raise ValidationError("Number min_value must be a number.")
            
            if max_val is not None and not isinstance(max_val, (int, float)):
                raise ValidationError("Number max_value must be a number.")
            
            if min_val is not None and max_val is not None and min_val >= max_val:
                raise ValidationError("Number min_value must be less than max_value.")
            
            if step is not None and (not isinstance(step, (int, float)) or step <= 0):
                raise ValidationError("Number step must be a positive number.")
        
        return True
    
    def get_field_types(self) -> List[Dict[str, str]]:
        """
        Get available field types with their display names.
        
        Returns:
            List[Dict[str, str]]: List of field types with value and label
        """
        return [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Field.FIELD_TYPES
        ]
