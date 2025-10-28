from typing import List
from django.db import transaction
from django.db.models import Max, F
from forms.models import Field, Form
from .base_repository import BaseRepository


class FieldRepository(BaseRepository):
    """Repository for Field model operations."""
    
    def __init__(self):
        super().__init__(Field)
    
    def get_by_form(self, form_id: str) -> List[Field]:
        """Get all fields for a specific form."""
        return list(Field.objects.filter(form_id=form_id).order_by('order_num'))
    
    def get_by_user(self, user_id: str) -> List[Field]:
        """Get all fields for user's forms."""
        return list(Field.objects.filter(form__created_by_id=user_id).order_by('form', 'order_num'))
    
    def get_max_order_for_form(self, form_id: str) -> int:
        """Get the maximum order number for a form."""
        max_order = Field.objects.filter(form_id=form_id).aggregate(
            max_order=Max('order_num')
        )['max_order']
        return max_order or 0
    
    def reorder_fields_after_delete(self, form_id: str, deleted_order: int) -> None:
        """Reorder fields after deletion."""
        with transaction.atomic():
            # Get fields with order_num > deleted_order
            fields_to_update = Field.objects.filter(
                form_id=form_id,
                order_num__gt=deleted_order
            ).order_by('order_num')
            
            # Temporarily set to large values to avoid conflicts
            for i, field in enumerate(fields_to_update):
                field.order_num = 999999 + i
                field.save(update_fields=['order_num'])
            
            # Update with correct order numbers
            for i, field in enumerate(fields_to_update):
                field.order_num = deleted_order + i
                field.save(update_fields=['order_num'])
    
    def reorder_fields_for_move(self, form_id: str, old_order: int, new_order: int, field_id: str) -> None:
        """Reorder fields when moving a field."""
        with transaction.atomic():
            # Temporarily set the moving field to a large value
            Field.objects.filter(id=field_id).update(order_num=999999)
            
            if new_order > old_order:
                # Moving down: shift fields between old_order+1 and new_order up
                Field.objects.filter(
                    form_id=form_id,
                    order_num__gt=old_order,
                    order_num__lte=new_order
                ).exclude(id=field_id).update(order_num=F('order_num') - 1)
            else:
                # Moving up: shift fields between new_order and old_order-1 down
                Field.objects.filter(
                    form_id=form_id,
                    order_num__gte=new_order,
                    order_num__lt=old_order
                ).exclude(id=field_id).update(order_num=F('order_num') + 1)
            
            # Set the moving field to its new order
            Field.objects.filter(id=field_id).update(order_num=new_order)
    
    def get_field_count_for_form(self, form_id: str) -> int:
        """Get the total number of fields for a form."""
        return Field.objects.filter(form_id=form_id).count()
