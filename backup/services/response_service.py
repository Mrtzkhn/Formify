from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from forms.models import Response, Answer, Form, Field
from forms.repositories.response_repository import ResponseRepository, AnswerRepository
from typing import Dict, List, Any

User = get_user_model()


class ResponseService:
    """Service layer for response operations with business logic."""
    
    def __init__(self):
        self.response_repository = ResponseRepository()
        self.answer_repository = AnswerRepository()
    
    def submit_response(self, form_id: str, answers_data: List[Dict[str, Any]], 
                       ip_address: str, user_agent: str, submitted_by: User = None) -> Response:
        """
        Submit a response to a form.
        
        Args:
            form_id: The form ID
            answers_data: List of answers with field_id and value
            ip_address: IP address of the submitter
            user_agent: User agent string
            submitted_by: User who submitted (optional)
            
        Returns:
            Response: The created response instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate form exists and is active
        form = get_object_or_404(Form, id=form_id)
        if not form.is_active:
            raise ValidationError("Cannot submit to inactive form.")
        
        # Validate required fields are answered
        required_fields = Field.objects.filter(form=form, is_required=True)
        answered_field_ids = {answer['field_id'] for answer in answers_data}
        
        missing_required_fields = []
        for field in required_fields:
            if str(field.id) not in answered_field_ids:
                missing_required_fields.append(field.label)
        
        if missing_required_fields:
            raise ValidationError(f"Required fields not answered: {', '.join(missing_required_fields)}")
        
        # Validate field IDs exist in the form
        form_field_ids = set(str(field.id) for field in form.fields.all())
        invalid_field_ids = []
        for answer in answers_data:
            if answer['field_id'] not in form_field_ids:
                invalid_field_ids.append(answer['field_id'])
        
        if invalid_field_ids:
            raise ValidationError(f"Invalid field IDs: {', '.join(invalid_field_ids)}")
        
        # Create response with answers
        response = self.response_repository.create_with_answers(
            form_id=form_id,
            answers_data=answers_data,
            ip_address=ip_address,
            user_agent=user_agent,
            submitted_by=submitted_by
        )
        
        return response
    
    def get_form_responses(self, user, form_id: str) -> List[Response]:
        """
        Get all responses for a specific form.
        
        Args:
            user: The authenticated user
            form_id: The form ID
            
        Returns:
            List[Response]: List of response instances
            
        Raises:
            ValidationError: If form doesn't exist or doesn't belong to user
        """
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return self.response_repository.get_by_form(form_id)
    
    def get_response_details(self, user, response_id: str) -> Response:
        """
        Get detailed response with answers.
        
        Args:
            user: The authenticated user
            response_id: The response ID
            
        Returns:
            Response: The response instance with answers
            
        Raises:
            ValidationError: If response doesn't exist or user doesn't have access
        """
        response = self.response_repository.get_response_with_answers(response_id)
        if not response:
            raise ValidationError("Response not found.")
        
        # Check if user has access (form owner or response submitter)
        if response.form.created_by != user and response.submitted_by != user:
            raise ValidationError("You don't have permission to view this response.")
        
        return response
    
    def get_user_responses(self, user) -> List[Response]:
        """
        Get all responses submitted by a user.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[Response]: List of response instances
        """
        return self.response_repository.get_by_user(str(user.id))
    
    def get_form_owner_responses(self, user) -> List[Response]:
        """
        Get all responses for forms owned by a user.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[Response]: List of response instances
        """
        return self.response_repository.get_by_form_owner(str(user.id))
    
    def delete_response(self, user, response_id: str) -> bool:
        """
        Delete a response.
        
        Args:
            user: The authenticated user
            response_id: The response ID
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ValidationError: If response doesn't exist or user doesn't have permission
        """
        response = self.response_repository.get_by_id(response_id)
        if not response:
            raise ValidationError("Response not found.")
        
        # Check if user has permission (form owner or response submitter)
        if response.form.created_by != user and response.submitted_by != user:
            raise ValidationError("You don't have permission to delete this response.")
        
        return self.response_repository.delete(response)


class AnswerService:
    """Service layer for answer operations with business logic."""
    
    def __init__(self):
        self.answer_repository = AnswerRepository()
        self.response_repository = ResponseRepository()
    
    def get_response_answers(self, user, response_id: str) -> List[Answer]:
        """
        Get all answers for a specific response.
        
        Args:
            user: The authenticated user
            response_id: The response ID
            
        Returns:
            List[Answer]: List of answer instances
            
        Raises:
            ValidationError: If response doesn't exist or user doesn't have access
        """
        # Get response to validate access
        response = self.response_repository.get_by_id(response_id)
        if not response:
            raise ValidationError("Response not found.")
        
        # Check if user has access (form owner or response submitter)
        if response.form.created_by != user and response.submitted_by != user:
            raise ValidationError("You don't have permission to view these answers.")
        
        return self.answer_repository.get_by_response(response_id)
    
    def get_field_answers(self, user, field_id: str) -> List[Answer]:
        """
        Get all answers for a specific field.
        
        Args:
            user: The authenticated user
            field_id: The field ID
            
        Returns:
            List[Answer]: List of answer instances
            
        Raises:
            ValidationError: If field doesn't exist or doesn't belong to user
        """
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        return self.answer_repository.get_by_field(field_id)
    
    def get_field_statistics(self, user, field_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific field.
        
        Args:
            user: The authenticated user
            field_id: The field ID
            
        Returns:
            Dict[str, Any]: Field statistics
            
        Raises:
            ValidationError: If field doesn't exist or doesn't belong to user
        """
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        return self.answer_repository.get_field_statistics(field_id)
    
    def get_form_answers(self, user, form_id: str) -> List[Answer]:
        """
        Get all answers for fields in a specific form.
        
        Args:
            user: The authenticated user
            form_id: The form ID
            
        Returns:
            List[Answer]: List of answer instances
            
        Raises:
            ValidationError: If form doesn't exist or doesn't belong to user
        """
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return self.answer_repository.get_by_form(form_id)
