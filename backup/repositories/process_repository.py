from typing import List
from django.db import transaction
from django.db.models import Max, F
from forms.models import Process, ProcessStep
from .base_repository import BaseRepository


class ProcessRepository(BaseRepository):
    """Repository for Process model operations."""
    
    def __init__(self):
        super().__init__(Process)
    
    def get_by_user(self, user_id: str) -> List[Process]:
        """Get all processes for a specific user."""
        return list(Process.objects.filter(created_by_id=user_id).order_by('-created_at'))
    
    def get_public_processes(self) -> List[Process]:
        """Get all public processes."""
        return list(Process.objects.filter(is_public=True, is_active=True).order_by('-created_at'))
    
    def get_max_order_for_process(self, process_id: str) -> int:
        """Get the maximum order number for a process."""
        max_order = ProcessStep.objects.filter(process_id=process_id).aggregate(
            max_order=Max('order_num')
        )['max_order']
        return max_order or 0
    
    def get_step_count_for_process(self, process_id: str) -> int:
        """Get the total number of steps for a process."""
        return ProcessStep.objects.filter(process_id=process_id).count()


class ProcessStepRepository(BaseRepository):
    """Repository for ProcessStep model operations."""
    
    def __init__(self):
        super().__init__(ProcessStep)
    
    def get_by_process(self, process_id: str) -> List[ProcessStep]:
        """Get all steps for a specific process."""
        return list(ProcessStep.objects.filter(process_id=process_id).order_by('order_num'))
    
    def get_by_user(self, user_id: str) -> List[ProcessStep]:
        """Get all steps for user's processes."""
        return list(ProcessStep.objects.filter(process__created_by_id=user_id).order_by('process', 'order_num'))
    
    def reorder_steps_after_delete(self, process_id: str, deleted_order: int) -> None:
        """Reorder steps after deletion."""
        with transaction.atomic():
            # Get steps with order_num > deleted_order
            steps_to_update = ProcessStep.objects.filter(
                process_id=process_id,
                order_num__gt=deleted_order
            ).order_by('order_num')
            
            # Temporarily set to large values to avoid conflicts
            for i, step in enumerate(steps_to_update):
                step.order_num = 999999 + i
                step.save(update_fields=['order_num'])
            
            # Update with correct order numbers
            for i, step in enumerate(steps_to_update):
                step.order_num = deleted_order + i
                step.save(update_fields=['order_num'])
    
    def reorder_steps_for_move(self, process_id: str, old_order: int, new_order: int, step_id: str) -> None:
        """Reorder steps when moving a step."""
        with transaction.atomic():
            # Temporarily set the moving step to a large value
            ProcessStep.objects.filter(id=step_id).update(order_num=999999)
            
            if new_order > old_order:
                # Moving down: shift steps between old_order+1 and new_order up
                ProcessStep.objects.filter(
                    process_id=process_id,
                    order_num__gt=old_order,
                    order_num__lte=new_order
                ).exclude(id=step_id).update(order_num=F('order_num') - 1)
            else:
                # Moving up: shift steps between new_order and old_order-1 down
                ProcessStep.objects.filter(
                    process_id=process_id,
                    order_num__gte=new_order,
                    order_num__lt=old_order
                ).exclude(id=step_id).update(order_num=F('order_num') + 1)
            
            # Set the moving step to its new order
            ProcessStep.objects.filter(id=step_id).update(order_num=new_order)
