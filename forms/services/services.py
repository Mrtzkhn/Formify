from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import Max, F
from django.shortcuts import get_object_or_404
from forms.models import Field, Form
from typing import Dict, List, Any, Optional


class FieldService:
    """Service layer for field operations with business logic."""
    
    @staticmethod
    def create_field(user, form_id: str, field_data: Dict[str, Any]) -> Field:
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
            max_order = Field.objects.filter(form=form).aggregate(
                max_order=Max('order_num')
            )['max_order'] or 0
            field_data['order_num'] = max_order + 1
        
        # Validate field options
        field_type = field_data.get('field_type')
        if field_type:
            FieldService.validate_field_options(
                field_type, 
                field_data.get('options', {})
            )
        
        # Create the field
        field = Field.objects.create(
            form=form,
            **field_data
        )
        
        return field
    
    @staticmethod
    def get_user_fields(user) -> List[Field]:
        """
        Get all fields for user's forms.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[Field]: List of fields belonging to user's forms
        """
        return Field.objects.filter(form__created_by=user).order_by('form', 'order_num')
    
    @staticmethod
    def get_form_fields(user, form_id: str) -> List[Field]:
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
        return Field.objects.filter(form=form).order_by('order_num')
    
    @staticmethod
    def update_field(user, field_id: str, field_data: Dict[str, Any]) -> Field:
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
            FieldService.validate_field_options(field_type, options)
        
        # Update the field
        for key, value in field_data.items():
            setattr(field, key, value)
        
        field.save()
        return field
    
    @staticmethod
    def delete_field(user, field_id: str) -> bool:
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
        
        # Reorder remaining fields
        with transaction.atomic():
            # Get all fields in the same form with order_num > deleted field's order_num
            remaining_fields = Field.objects.filter(
                form=field.form,
                order_num__gt=field.order_num
            ).order_by('order_num')
            
            # Temporarily set order_num to large values to avoid conflicts
            for i, remaining_field in enumerate(remaining_fields):
                remaining_field.order_num = 999999 + i
                remaining_field.save(update_fields=['order_num'])
            
            # Delete the field
            field.delete()
            
            # Now update the remaining fields with correct order numbers
            for i, remaining_field in enumerate(remaining_fields):
                remaining_field.order_num = field.order_num + i
                remaining_field.save(update_fields=['order_num'])
        
        return True
    
    @staticmethod
    def reorder_field(user, field_id: str, new_order: int) -> Field:
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
        
        max_order = Field.objects.filter(form=field.form).count()
        if new_order > max_order:
            raise ValidationError(f"Order number cannot exceed {max_order}.")
        
        with transaction.atomic():
            old_order = field.order_num
            
            if new_order == old_order:
                return field
            
            # Temporarily set the field's order to a large value to avoid conflicts
            field.order_num = 999999
            field.save(update_fields=['order_num'])
            
            # Shift other fields to make room
            if new_order > old_order:
                # Moving down: shift fields between old_order+1 and new_order up
                Field.objects.filter(
                    form=field.form,
                    order_num__gt=old_order,
                    order_num__lte=new_order
                ).exclude(id=field.id).update(order_num=F('order_num') - 1)
            else:
                # Moving up: shift fields between new_order and old_order-1 down
                Field.objects.filter(
                    form=field.form,
                    order_num__gte=new_order,
                    order_num__lt=old_order
                ).exclude(id=field.id).update(order_num=F('order_num') + 1)
            
            # Update the field's order
            field.order_num = new_order
            field.save(update_fields=['order_num'])
        
        return field
    
    @staticmethod
    def validate_field_options(field_type: str, options: Dict[str, Any]) -> bool:
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
    
    @staticmethod
    def get_field_types() -> List[Dict[str, str]]:
        """
        Get available field types with their display names.
        
        Returns:
            List[Dict[str, str]]: List of field types with value and label
        """
        return [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Field.FIELD_TYPES
        ]
