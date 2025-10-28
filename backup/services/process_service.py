from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from forms.models import Process, ProcessStep
from forms.repositories.process_repository import ProcessRepository, ProcessStepRepository
from typing import Dict, List, Any


class ProcessService:
    """Service layer for process operations with business logic."""
    
    def __init__(self):
        self.process_repository = ProcessRepository()
        self.process_step_repository = ProcessStepRepository()
    
    def create_process(self, user, process_data: Dict[str, Any]) -> Process:
        """
        Create a new process.
        
        Args:
            user: The authenticated user
            process_data: Dictionary containing process data
            
        Returns:
            Process: The created process instance
            
        Raises:
            ValidationError: If process data is invalid
        """
        # Validate process type
        process_type = process_data.get('process_type')
        if process_type:
            self.validate_process_type(process_type)
        
        # Create the process
        process = self.process_repository.create(
            created_by=user,
            **process_data
        )
        
        return process
    
    def get_user_processes(self, user) -> List[Process]:
        """
        Get all processes for user.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[Process]: List of processes belonging to user
        """
        return self.process_repository.get_by_user(str(user.id))
    
    def get_public_processes(self) -> List[Process]:
        """
        Get all public processes.
        
        Returns:
            List[Process]: List of public processes
        """
        return self.process_repository.get_public_processes()
    
    def update_process(self, user, process_id: str, process_data: Dict[str, Any]) -> Process:
        """
        Update an existing process.
        
        Args:
            user: The authenticated user
            process_id: UUID of the process
            process_data: Dictionary containing updated process data
            
        Returns:
            Process: The updated process instance
            
        Raises:
            ValidationError: If process data is invalid
        """
        process = get_object_or_404(Process, id=process_id, created_by=user)
        
        # Validate process type if being updated
        if 'process_type' in process_data:
            self.validate_process_type(process_data['process_type'])
        
        # Update the process using repository
        return self.process_repository.update(process, **process_data)
    
    def delete_process(self, user, process_id: str) -> bool:
        """
        Delete a process.
        
        Args:
            user: The authenticated user
            process_id: UUID of the process
            
        Returns:
            bool: True if process was deleted
        """
        process = get_object_or_404(Process, id=process_id, created_by=user)
        
        # Delete the process (this will cascade delete all steps)
        self.process_repository.delete(process)
        
        return True
    
    def validate_process_type(self, process_type: str) -> bool:
        """
        Validate process type.
        
        Args:
            process_type: Type of the process
            
        Returns:
            bool: True if process type is valid
            
        Raises:
            ValidationError: If process type is invalid
        """
        valid_types = [choice[0] for choice in Process.PROCESS_TYPES]
        if process_type not in valid_types:
            raise ValidationError(f"Process type must be one of: {', '.join(valid_types)}")
        
        return True
    
    def get_process_types(self) -> List[Dict[str, str]]:
        """
        Get available process types with their display names.
        
        Returns:
            List[Dict[str, str]]: List of process types with value and label
        """
        return [{'value': pt[0], 'label': pt[1]} for pt in Process.PROCESS_TYPES]
    
    def get_process_by_id(self, process_id: str) -> Process:
        """
        Get a process by ID (for public access).
        
        Args:
            process_id: UUID of the process
            
        Returns:
            Process: The process instance or None if not found
        """
        return self.process_repository.get_by_id(process_id)
    
    def validate_process_access(self, process_id: str, password: str) -> bool:
        """
        Validate access to a private process with password.
        
        Args:
            process_id: UUID of the process
            password: Access password
            
        Returns:
            bool: True if access is granted
        """
        try:
            process = Process.objects.get(id=process_id, is_active=True)
            return process.access_password == password
        except Process.DoesNotExist:
            return False


class ProcessStepService:
    """Service layer for process step operations with business logic."""
    
    def __init__(self):
        self.process_repository = ProcessRepository()
        self.process_step_repository = ProcessStepRepository()
    
    def create_process_step(self, user, process_id: str, step_data: Dict[str, Any]) -> ProcessStep:
        """
        Create a new process step.
        
        Args:
            user: The authenticated user
            process_id: UUID of the process
            step_data: Dictionary containing step data
            
        Returns:
            ProcessStep: The created process step instance
            
        Raises:
            ValidationError: If step data is invalid
        """
        # Verify user owns the process
        process = get_object_or_404(Process, id=process_id, created_by=user)
        
        # Set default order number if not provided
        if 'order_num' not in step_data:
            max_order = self.process_repository.get_max_order_for_process(str(process.id))
            step_data['order_num'] = max_order + 1
        
        # Validate that the form belongs to the user
        form = step_data.get('form')
        if form and form.created_by != user:
            raise ValidationError("You can only use forms you created.")
        
        # Create the process step
        step = self.process_step_repository.create(
            process=process,
            **step_data
        )
        
        return step
    
    def get_user_process_steps(self, user) -> List[ProcessStep]:
        """
        Get all process steps for user's processes.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[ProcessStep]: List of process steps belonging to user's processes
        """
        return self.process_step_repository.get_by_user(str(user.id))
    
    def get_process_steps(self, user, process_id: str) -> List[ProcessStep]:
        """
        Get all steps for a specific process.
        
        Args:
            user: The authenticated user
            process_id: UUID of the process
            
        Returns:
            List[ProcessStep]: List of steps for the process
            
        Raises:
            ValidationError: If user doesn't own the process
        """
        process = get_object_or_404(Process, id=process_id, created_by=user)
        return self.process_step_repository.get_by_process(str(process.id))
    
    def update_process_step(self, user, step_id: str, step_data: Dict[str, Any]) -> ProcessStep:
        """
        Update an existing process step.
        
        Args:
            user: The authenticated user
            step_id: UUID of the process step
            step_data: Dictionary containing updated step data
            
        Returns:
            ProcessStep: The updated process step instance
            
        Raises:
            ValidationError: If step data is invalid
        """
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        
        # Update the process step using repository
        return self.process_step_repository.update(step, **step_data)
    
    def delete_process_step(self, user, step_id: str) -> bool:
        """
        Delete a process step.
        
        Args:
            user: The authenticated user
            step_id: UUID of the process step
            
        Returns:
            bool: True if step was deleted
        """
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        
        # Store the order number and process ID before deletion
        deleted_order = step.order_num
        process_id = str(step.process.id)
        
        # Delete the step
        self.process_step_repository.delete(step)
        
        # Reorder remaining steps using repository
        self.process_step_repository.reorder_steps_after_delete(process_id, deleted_order)
        
        return True
    
    def reorder_process_step(self, user, step_id: str, new_order: int) -> ProcessStep:
        """
        Reorder a process step within its process.
        
        Args:
            user: The authenticated user
            step_id: UUID of the process step
            new_order: New order number for the step
            
        Returns:
            ProcessStep: The updated process step instance
            
        Raises:
            ValidationError: If new_order is invalid
        """
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        
        if new_order < 1:
            raise ValidationError("Order number must be at least 1.")
        
        # Get max order for the process
        max_order = self.process_repository.get_max_order_for_process(str(step.process.id))
        if new_order > max_order:
            raise ValidationError(f"Order number cannot exceed {max_order}.")
        
        old_order = step.order_num
        
        # Use repository to handle reordering
        self.process_step_repository.reorder_steps_for_move(
            str(step.process.id),
            old_order,
            new_order,
            str(step.id)
        )
        
        # Refresh and return the step
        step.refresh_from_db()
        return step
    
    def update_process_step(self, user, step_id: str, step_data: Dict[str, Any]) -> ProcessStep:
        """
        Update an existing process step.
        
        Args:
            user: The authenticated user
            step_id: UUID of the process step
            step_data: Dictionary containing updated step data
            
        Returns:
            ProcessStep: The updated process step instance
            
        Raises:
            ValidationError: If step data is invalid
        """
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        
        # Update the process step using repository
        return self.process_step_repository.update(step, **step_data)
    
    def delete_process_step(self, user, step_id: str) -> bool:
        """
        Delete a process step.
        
        Args:
            user: The authenticated user
            step_id: UUID of the process step
            
        Returns:
            bool: True if step was deleted
        """
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        
        # Store the order number and process ID before deletion
        deleted_order = step.order_num
        process_id = str(step.process.id)
        
        # Delete the step
        self.process_step_repository.delete(step)
        
        # Reorder remaining steps using repository
        self.process_step_repository.reorder_steps_after_delete(process_id, deleted_order)
        
        return True
    
    def reorder_process_step(self, user, step_id: str, new_order: int) -> ProcessStep:
        """
        Reorder a process step within its process.
        
        Args:
            user: The authenticated user
            step_id: UUID of the process step
            new_order: New order number for the step
            
        Returns:
            ProcessStep: The updated process step instance
            
        Raises:
            ValidationError: If new_order is invalid
        """
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        
        if new_order < 1:
            raise ValidationError("Order number must be at least 1.")
        
        # Get max order for the process
        max_order = self.process_repository.get_max_order_for_process(str(step.process.id))
        if new_order > max_order:
            raise ValidationError(f"Order number cannot exceed {max_order}.")
        
        old_order = step.order_num
        
        # Use repository to handle reordering
        self.process_step_repository.reorder_steps_for_move(
            str(step.process.id),
            old_order,
            new_order,
            str(step.id)
        )
        
        # Refresh and return the step
        step.refresh_from_db()
        return step
    
    def get_process_steps_public(self, process_id: str) -> List[ProcessStep]:
        """
        Get all steps for a specific process (for public access).
        
        Args:
            process_id: UUID of the process
            
        Returns:
            List[ProcessStep]: List of steps for the process
        """
        return self.process_step_repository.get_by_process(process_id)
    
    def get_process_step_by_id(self, step_id: str) -> ProcessStep:
        """
        Get a process step by ID (for public access).
        
        Args:
            step_id: UUID of the process step
            
        Returns:
            ProcessStep: The process step instance or None if not found
        """
        return self.process_step_repository.get_by_id(step_id)