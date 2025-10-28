from typing import List, Dict, Any
from django.db import transaction
from django.contrib.auth import get_user_model
from forms.models import Response, Answer, Field
from .base_repository import BaseRepository

User = get_user_model()


class ResponseRepository(BaseRepository):
    """Repository for Response model operations."""
    
    def __init__(self):
        super().__init__(Response)
    
    def get_by_form(self, form_id: str) -> List[Response]:
        """Get all responses for a specific form."""
        return list(Response.objects.filter(form_id=form_id).order_by('-submitted_at'))
    
    def get_by_user(self, user_id: str) -> List[Response]:
        """Get all responses submitted by a specific user."""
        return list(Response.objects.filter(submitted_by_id=user_id).order_by('-submitted_at'))
    
    def get_by_form_owner(self, user_id: str) -> List[Response]:
        """Get all responses for forms owned by a specific user."""
        return list(Response.objects.filter(
            form__created_by_id=user_id
        ).order_by('-submitted_at'))
    
    def create_with_answers(self, form_id: str, answers_data: List[Dict[str, Any]], 
                          ip_address: str, user_agent: str, submitted_by: User = None) -> Response:
        """Create a response with its answers in a single transaction."""
        with transaction.atomic():
            # Create the response
            response = Response.objects.create(
                form_id=form_id,
                submitted_by=submitted_by,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Create answers
            answers = []
            for answer_data in answers_data:
                field_id = answer_data['field_id']
                value = answer_data['value']
                
                # Validate field exists and belongs to the form
                try:
                    field = Field.objects.get(id=field_id, form_id=form_id)
                except Field.DoesNotExist:
                    raise ValueError(f"Field {field_id} does not exist in form {form_id}")
                
                answer = Answer.objects.create(
                    response=response,
                    field=field,
                    value=value
                )
                answers.append(answer)
            
            return response
    
    def get_response_with_answers(self, response_id: str) -> Response:
        """Get a response with its answers."""
        try:
            return Response.objects.prefetch_related('answers__field').get(id=response_id)
        except Response.DoesNotExist:
            return None


class AnswerRepository(BaseRepository):
    """Repository for Answer model operations."""
    
    def __init__(self):
        super().__init__(Answer)
    
    def get_by_response(self, response_id: str) -> List[Answer]:
        """Get all answers for a specific response."""
        return list(Answer.objects.filter(response_id=response_id).order_by('field__order_num'))
    
    def get_by_field(self, field_id: str) -> List[Answer]:
        """Get all answers for a specific field."""
        return list(Answer.objects.filter(field_id=field_id).order_by('-created_at'))
    
    def get_by_form(self, form_id: str) -> List[Answer]:
        """Get all answers for fields in a specific form."""
        return list(Answer.objects.filter(
            field__form_id=form_id
        ).order_by('-created_at'))
    
    def get_field_statistics(self, field_id: str) -> Dict[str, Any]:
        """Get statistics for a specific field."""
        answers = Answer.objects.filter(field_id=field_id)
        
        stats = {
            'total_answers': answers.count(),
            'unique_values': answers.values('value').distinct().count(),
            'most_common_value': None,
            'value_counts': {}
        }
        
        if stats['total_answers'] > 0:
            # Get value counts
            value_counts = {}
            for answer in answers:
                value = answer.value
                value_counts[value] = value_counts.get(value, 0) + 1
            
            stats['value_counts'] = value_counts
            
            # Find most common value
            if value_counts:
                stats['most_common_value'] = max(value_counts, key=value_counts.get)
        
        return stats
