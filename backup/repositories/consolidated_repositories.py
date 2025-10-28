from abc import ABC
from typing import List, Optional, Any, Dict
from django.db import models, transaction
from django.db.models import Max, F, Q
from django.contrib.auth import get_user_model
from forms.models import (
    Field, Form, Process, ProcessStep, Category, EntityCategory, 
    Response as FormResponse, Answer, FormView
)

User = get_user_model()


# =============================================================================
# BASE REPOSITORY
# =============================================================================

class BaseRepository(ABC):
    """Base repository class for data access layer."""
    
    def __init__(self, model: models.Model):
        self.model = model
    
    def get_by_id(self, id: Any) -> Optional[models.Model]:
        """Get a single object by ID."""
        try:
            return self.model.objects.get(id=id)
        except self.model.DoesNotExist:
            return None
    
    def get_all(self) -> List[models.Model]:
        """Get all objects."""
        return list(self.model.objects.all())
    
    def create(self, **kwargs) -> models.Model:
        """Create a new object."""
        return self.model.objects.create(**kwargs)
    
    def update(self, obj: models.Model, **kwargs) -> models.Model:
        """Update an existing object."""
        for key, value in kwargs.items():
            setattr(obj, key, value)
        obj.save()
        return obj
    
    def delete(self, obj: models.Model) -> bool:
        """Delete an object."""
        obj.delete()
        return True
    
    def exists(self, **kwargs) -> bool:
        """Check if an object exists."""
        return self.model.objects.filter(**kwargs).exists()


# =============================================================================
# FIELD REPOSITORY
# =============================================================================

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
        Field.objects.filter(
            form_id=form_id,
            order_num__gt=deleted_order
        ).update(order_num=F('order_num') - 1)
    
    def reorder_fields_for_move(self, form_id: str, old_order: int, new_order: int, field_id: str) -> None:
        """Reorder fields when moving a field to a new position."""
        with transaction.atomic():
            if old_order < new_order:
                # Moving down: shift fields between old and new position up
                Field.objects.filter(
                    form_id=form_id,
                    order_num__gt=old_order,
                    order_num__lte=new_order
                ).exclude(id=field_id).update(order_num=F('order_num') - 1)
            else:
                # Moving up: shift fields between new and old position down
                Field.objects.filter(
                    form_id=form_id,
                    order_num__gte=new_order,
                    order_num__lt=old_order
                ).exclude(id=field_id).update(order_num=F('order_num') + 1)
            
            # Update the moved field
            Field.objects.filter(id=field_id).update(order_num=new_order)
    
    def get_field_count_for_form(self, form_id: str) -> int:
        """Get the total number of fields for a form."""
        return Field.objects.filter(form_id=form_id).count()


# =============================================================================
# FORM REPOSITORY
# =============================================================================

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
            
            # If form is private, only the owner can access it
            if user and form.created_by == user:
                return form
            
            # If form is private and user is not the owner, raise exception
            raise Form.DoesNotExist("Form not found or access denied")
            
        except Form.DoesNotExist:
            raise Form.DoesNotExist("Form not found or access denied")
    
    def get_public_form_by_id(self, form_id: str) -> Optional[Form]:
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
        """Validate password for private form access."""
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
    
    def get_form_with_fields(self, form_id: str) -> Optional[Form]:
        """Get a form with its fields."""
        try:
            return Form.objects.prefetch_related('fields').get(id=form_id)
        except Form.DoesNotExist:
            return None


# =============================================================================
# PROCESS REPOSITORY
# =============================================================================

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
    
    def get_by_id_with_access_check(self, process_id: str, user=None) -> Process:
        """Get process by ID with access control."""
        try:
            process = Process.objects.get(id=process_id, is_active=True)
            
            # If process is public, anyone can access it
            if process.is_public:
                return process
            
            # If process is private, only the owner can access it
            if user and process.created_by == user:
                return process
            
            # If process is private and user is not the owner, raise exception
            raise Process.DoesNotExist("Process not found or access denied")
            
        except Process.DoesNotExist:
            raise Process.DoesNotExist("Process not found or access denied")
    
    def get_public_process_by_id(self, process_id: str) -> Optional[Process]:
        """Get a public process by ID."""
        try:
            return Process.objects.get(
                id=process_id, 
                is_public=True, 
                is_active=True
            )
        except Process.DoesNotExist:
            return None
    
    def validate_password(self, process_id: str, password: str) -> bool:
        """Validate password for private process access."""
        try:
            process = Process.objects.get(id=process_id, is_active=True)
            return process.access_password == password
        except Process.DoesNotExist:
            return False


# =============================================================================
# PROCESS STEP REPOSITORY
# =============================================================================

class ProcessStepRepository(BaseRepository):
    """Repository for ProcessStep model operations."""
    
    def __init__(self):
        super().__init__(ProcessStep)
    
    def get_by_process(self, process_id: str) -> List[ProcessStep]:
        """Get all steps for a specific process."""
        return list(ProcessStep.objects.filter(process_id=process_id).order_by('order_num'))
    
    def get_by_user(self, user_id: str) -> List[ProcessStep]:
        """Get all process steps for user's processes."""
        return list(ProcessStep.objects.filter(process__created_by_id=user_id).order_by('process', 'order_num'))
    
    def get_max_order_for_process(self, process_id: str) -> int:
        """Get the maximum order number for a process."""
        max_order = ProcessStep.objects.filter(process_id=process_id).aggregate(
            max_order=Max('order_num')
        )['max_order']
        return max_order or 0
    
    def reorder_steps_after_delete(self, process_id: str, deleted_order: int) -> None:
        """Reorder steps after deletion."""
        ProcessStep.objects.filter(
            process_id=process_id,
            order_num__gt=deleted_order
        ).update(order_num=F('order_num') - 1)
    
    def reorder_steps_for_move(self, process_id: str, old_order: int, new_order: int, step_id: str) -> None:
        """Reorder steps when moving a step to a new position."""
        with transaction.atomic():
            if old_order < new_order:
                # Moving down: shift steps between old and new position up
                ProcessStep.objects.filter(
                    process_id=process_id,
                    order_num__gt=old_order,
                    order_num__lte=new_order
                ).exclude(id=step_id).update(order_num=F('order_num') - 1)
            else:
                # Moving up: shift steps between new and old position down
                ProcessStep.objects.filter(
                    process_id=process_id,
                    order_num__gte=new_order,
                    order_num__lt=old_order
                ).exclude(id=step_id).update(order_num=F('order_num') + 1)
            
            # Update the moved step
            ProcessStep.objects.filter(id=step_id).update(order_num=new_order)
    
    def get_step_count_for_process(self, process_id: str) -> int:
        """Get the total number of steps for a process."""
        return ProcessStep.objects.filter(process_id=process_id).count()


# =============================================================================
# CATEGORY REPOSITORY
# =============================================================================

class CategoryRepository(BaseRepository):
    """Repository for Category model operations."""
    
    def __init__(self):
        super().__init__(Category)
    
    def get_by_user(self, user_id: str) -> List[Category]:
        """Get all categories for a specific user."""
        return list(Category.objects.filter(created_by_id=user_id).order_by('name'))
    
    def get_by_name(self, name: str, user_id: str) -> Category:
        """Get a category by name for a specific user."""
        try:
            return Category.objects.get(name=name, created_by_id=user_id)
        except Category.DoesNotExist:
            return None
    
    def exists_by_name(self, name: str, user_id: str) -> bool:
        """Check if a category exists by name for a specific user."""
        return Category.objects.filter(name=name, created_by_id=user_id).exists()


# =============================================================================
# ENTITY CATEGORY REPOSITORY
# =============================================================================

class EntityCategoryRepository(BaseRepository):
    """Repository for EntityCategory model operations."""
    
    def __init__(self):
        super().__init__(EntityCategory)
    
    def get_by_entity(self, entity_type: str, entity_id: str) -> List[EntityCategory]:
        """Get all categories for a specific entity."""
        return list(EntityCategory.objects.filter(
            entity_type=entity_type, 
            entity_id=entity_id
        ).order_by('-created_at'))
    
    def get_by_user(self, user_id: str) -> List[EntityCategory]:
        """Get all entity categories for user's entities."""
        return list(EntityCategory.objects.filter(
            Q(entity_type='form', entity_id__in=Form.objects.filter(created_by_id=user_id).values_list('id', flat=True)) |
            Q(entity_type='process', entity_id__in=Process.objects.filter(created_by_id=user_id).values_list('id', flat=True))
        ).order_by('-created_at'))
    
    def exists_by_entity_and_category(self, entity_type: str, entity_id: str, category_id: str) -> bool:
        """Check if an entity category association exists."""
        return EntityCategory.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id,
            category_id=category_id
        ).exists()


# =============================================================================
# RESPONSE REPOSITORY
# =============================================================================

class ResponseRepository(BaseRepository):
    """Repository for Response model operations."""
    
    def __init__(self):
        super().__init__(FormResponse)
    
    def get_by_form(self, form_id: str) -> List[FormResponse]:
        """Get all responses for a specific form."""
        return list(FormResponse.objects.filter(form_id=form_id).order_by('-submitted_at'))
    
    def get_by_user(self, user_id: str) -> List[FormResponse]:
        """Get all responses for user's forms."""
        return list(FormResponse.objects.filter(form__created_by_id=user_id).order_by('-submitted_at'))
    
    def get_response_count_for_form(self, form_id: str) -> int:
        """Get the total number of responses for a form."""
        return FormResponse.objects.filter(form_id=form_id).count()
    
    def get_responses_by_date_range(self, form_id: str, start_date, end_date) -> List[FormResponse]:
        """Get responses for a form within a date range."""
        return list(FormResponse.objects.filter(
            form_id=form_id,
            submitted_at__gte=start_date,
            submitted_at__lte=end_date
        ).order_by('-submitted_at'))
    
    def get_analytics_data(self, form_id: str) -> Dict[str, Any]:
        """Get analytics data for a form."""
        responses = FormResponse.objects.filter(form_id=form_id)
        
        return {
            'total_responses': responses.count(),
            'unique_submitters': responses.values('submitted_by').distinct().count(),
            'responses_by_date': list(responses.extra(
                select={'date': 'DATE(submitted_at)'}
            ).values('date').annotate(count=models.Count('id')).order_by('date')),
            'responses_by_ip': list(responses.values('ip_address').annotate(count=models.Count('id')).order_by('-count')[:10])
        }


# =============================================================================
# ANSWER REPOSITORY
# =============================================================================

class AnswerRepository(BaseRepository):
    """Repository for Answer model operations."""
    
    def __init__(self):
        super().__init__(Answer)
    
    def get_by_response(self, response_id: str) -> List[Answer]:
        """Get all answers for a specific response."""
        return list(Answer.objects.filter(response_id=response_id).order_by('field__order_num'))
    
    def get_by_field(self, field_id: str) -> List[Answer]:
        """Get all answers for a specific field."""
        return list(Answer.objects.filter(field_id=field_id).order_by('-response__submitted_at'))
    
    def get_by_user(self, user_id: str) -> List[Answer]:
        """Get all answers for user's responses."""
        return list(Answer.objects.filter(response__form__created_by_id=user_id).order_by('-response__submitted_at'))
    
    def get_answer_count_for_field(self, field_id: str) -> int:
        """Get the total number of answers for a field."""
        return Answer.objects.filter(field_id=field_id).count()
    
    def get_field_statistics(self, field_id: str) -> Dict[str, Any]:
        """Get statistics for a field."""
        answers = Answer.objects.filter(field_id=field_id)
        
        return {
            'total_answers': answers.count(),
            'unique_values': answers.values('value').distinct().count(),
            'most_common_values': list(answers.values('value').annotate(count=models.Count('id')).order_by('-count')[:10]),
            'answers_by_date': list(answers.extra(
                select={'date': 'DATE(response__submitted_at)'}
            ).values('date').annotate(count=models.Count('id')).order_by('date'))
        }
