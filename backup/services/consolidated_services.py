from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from forms.models import (
    Field, Form, Process, ProcessStep, Category, EntityCategory, 
    Response as FormResponse, Answer, FormView
)
from forms.repositories.field_repository import FieldRepository
from forms.repositories.form_repository import FormRepository
from forms.repositories.process_repository import ProcessRepository, ProcessStepRepository
from forms.repositories.category_repository import CategoryRepository, EntityCategoryRepository
from forms.repositories.response_repository import ResponseRepository, AnswerRepository
from typing import Dict, List, Any


# =============================================================================
# FIELD SERVICE
# =============================================================================

class FieldService:
    """Service layer for field operations with business logic."""
    
    def __init__(self):
        self.field_repository = FieldRepository()
    
    def create_field(self, user, form_id: str, field_data: Dict[str, Any]) -> Field:
        """Create a new field for a form."""
        form = get_object_or_404(Form, id=form_id, created_by=user)
        
        if 'order_num' not in field_data:
            max_order = self.field_repository.get_max_order_for_form(str(form.id))
            field_data['order_num'] = max_order + 1
        
        field_type = field_data.get('field_type')
        if field_type:
            self.validate_field_options(
                field_type, 
                field_data.get('options', {})
            )
        
        field = self.field_repository.create(
            form=form,
            **field_data
        )
        
        return field
    
    def get_user_fields(self, user) -> List[Field]:
        """Get all fields for user's forms."""
        return self.field_repository.get_by_user(str(user.id))
    
    def get_form_fields(self, user, form_id: str) -> List[Field]:
        """Get all fields for a specific form."""
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return self.field_repository.get_by_form(str(form.id))
    
    def get_field(self, user, field_id: str) -> Field:
        """Get a specific field."""
        return get_object_or_404(Field, id=field_id, form__created_by=user)
    
    def update_field(self, user, field_id: str, field_data: Dict[str, Any]) -> Field:
        """Update an existing field."""
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        
        if 'field_type' in field_data or 'options' in field_data:
            field_type = field_data.get('field_type', field.field_type)
            options = field_data.get('options', field.options)
            self.validate_field_options(field_type, options)
        
        return self.field_repository.update(field, **field_data)
    
    def delete_field(self, user, field_id: str) -> bool:
        """Delete a field."""
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        
        deleted_order = field.order_num
        form_id = str(field.form.id)
        
        self.field_repository.delete(field)
        self.field_repository.reorder_fields_after_delete(form_id, deleted_order)
        
        return True
    
    def reorder_field(self, user, field_id: str, new_order: int) -> Field:
        """Reorder a field within its form."""
        field = get_object_or_404(Field, id=field_id, form__created_by=user)
        
        if new_order < 1:
            raise ValidationError("Order number must be at least 1.")
        
        max_order = self.field_repository.get_field_count_for_form(str(field.form.id))
        if new_order > max_order:
            raise ValidationError(f"Order number cannot exceed {max_order}.")
        
        old_order = field.order_num
        
        if new_order == old_order:
            return field
        
        self.field_repository.reorder_fields_for_move(
            str(field.form.id), 
            old_order, 
            new_order, 
            str(field.id)
        )
        
        field.refresh_from_db()
        return field
    
    def validate_field_options(self, field_type: str, options: Dict[str, Any]) -> bool:
        """Validate field options based on field type."""
        if field_type in ['select', 'checkbox']:
            choices = options.get('choices', [])
            if not choices:
                raise ValidationError(f"Field type '{field_type}' requires choices in options.")
            
            for choice in choices:
                if not isinstance(choice, dict) or 'value' not in choice or 'label' not in choice:
                    raise ValidationError("Each choice must have 'value' and 'label' keys.")
        
        return True
    
    def get_field_types(self) -> List[Dict[str, str]]:
        """Get available field types with their display names."""
        return [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Field.FIELD_TYPES
        ]


# =============================================================================
# FORM SERVICE
# =============================================================================

class FormService:
    """Service layer for form operations with business logic."""
    
    def __init__(self):
        self.form_repository = FormRepository()
    
    def create_form(self, user, form_data: Dict[str, Any]) -> Form:
        """Create a new form."""
        is_public = form_data.get('is_public', True)
        access_password = form_data.get('access_password')

        if not is_public and not access_password:
            raise ValidationError("Private forms require an access password.")

        return self.form_repository.create(created_by=user, **form_data)

    def get_user_forms(self, user) -> List[Form]:
        """Get all forms for a specific user."""
        return self.form_repository.get_by_user(str(user.id))

    def get_form(self, user, form_id: str) -> Form:
        """Get a specific form for a user."""
        return get_object_or_404(Form, id=form_id, created_by=user)

    def update_form(self, user, form_id: str, form_data: Dict[str, Any]) -> Form:
        """Update an existing form."""
        form = get_object_or_404(Form, id=form_id, created_by=user)

        is_public = form_data.get('is_public', form.is_public)
        access_password = form_data.get('access_password', form.access_password)

        if not is_public and not access_password:
            raise ValidationError("Private forms require an access password.")

        return self.form_repository.update(form, **form_data)

    def delete_form(self, user, form_id: str) -> bool:
        """Delete a form."""
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return self.form_repository.delete(form)

    def get_public_forms(self) -> List[Form]:
        """Get all public forms."""
        return self.form_repository.get_public_forms()

    def get_public_form(self, form_id: str) -> Form:
        """Get a public form by ID."""
        return self.form_repository.get_public_form_by_id(form_id)

    def validate_form_access(self, form_id: str, password: str = None) -> Form:
        """Validate access to a form (public or with password)."""
        try:
            form = Form.objects.get(id=form_id, is_active=True)
        except Form.DoesNotExist:
            raise ValidationError("Form not found or inactive.")

        if form.is_public:
            return form

        if not password:
            raise ValidationError("This form requires a password.")

        if not self.form_repository.validate_password(form_id, password):
            raise ValidationError("Invalid password.")

        return form

    def track_form_view(self, form: Form, ip_address: str, user_agent: str) -> FormView:
        """Track a form view."""
        return self.form_repository.track_view(form, ip_address, user_agent)


# =============================================================================
# PROCESS SERVICE
# =============================================================================

class ProcessService:
    """Service layer for process operations with business logic."""
    
    def __init__(self):
        self.process_repository = ProcessRepository()
        self.process_step_repository = ProcessStepRepository()
    
    def create_process(self, user, process_data: Dict[str, Any]) -> Process:
        """Create a new process."""
        is_public = process_data.get('is_public', True)
        access_password = process_data.get('access_password')

        if not is_public and not access_password:
            raise ValidationError("Private processes require an access password.")

        return self.process_repository.create(created_by=user, **process_data)

    def get_user_processes(self, user) -> List[Process]:
        """Get all processes for a specific user."""
        return self.process_repository.get_by_user(str(user.id))

    def get_process(self, user, process_id: str) -> Process:
        """Get a specific process for a user."""
        return get_object_or_404(Process, id=process_id, created_by=user)

    def update_process(self, user, process_id: str, process_data: Dict[str, Any]) -> Process:
        """Update an existing process."""
        process = get_object_or_404(Process, id=process_id, created_by=user)

        is_public = process_data.get('is_public', process.is_public)
        access_password = process_data.get('access_password', process.access_password)

        if not is_public and not access_password:
            raise ValidationError("Private processes require an access password.")

        return self.process_repository.update(process, **process_data)

    def delete_process(self, user, process_id: str) -> bool:
        """Delete a process."""
        process = get_object_or_404(Process, id=process_id, created_by=user)
        return self.process_repository.delete(process)

    def get_public_processes(self) -> List[Process]:
        """Get all public processes."""
        return self.process_repository.get_public_processes()

    def get_process_by_id(self, process_id: str) -> Process:
        """Get a process by ID (for public access)."""
        try:
            return Process.objects.get(id=process_id, is_active=True)
        except Process.DoesNotExist:
            return None

    def validate_process_access(self, process_id: str, password: str = None) -> Process:
        """Validate access to a process (public or with password)."""
        try:
            process = Process.objects.get(id=process_id, is_active=True)
        except Process.DoesNotExist:
            raise ValidationError("Process not found or inactive.")

        if process.is_public:
            return process

        if not password:
            raise ValidationError("This process requires a password.")

        if not self.process_repository.validate_password(process_id, password):
            raise ValidationError("Invalid password.")

        return process


class ProcessStepService:
    """Service layer for process step operations with business logic."""

    def __init__(self):
        self.process_repository = ProcessRepository()
        self.process_step_repository = ProcessStepRepository()

    def create_process_step(self, user, step_data: Dict[str, Any]) -> ProcessStep:
        """Create a new process step."""
        process_id = step_data['process'].id
        form_id = step_data['form'].id

        # Verify user owns the process
        process = get_object_or_404(Process, id=process_id, created_by=user)
        
        # Verify user owns the form
        form = get_object_or_404(Form, id=form_id, created_by=user)

        # Set default order number if not provided
        if 'order_num' not in step_data:
            max_order = self.process_step_repository.get_max_order_for_process(str(process.id))
            step_data['order_num'] = max_order + 1

        return self.process_step_repository.create(
            process=process,
            form=form,
            **step_data
        )

    def get_user_process_steps(self, user) -> List[ProcessStep]:
        """Get all process steps for user's processes."""
        return self.process_step_repository.get_by_user(str(user.id))

    def get_process_steps(self, user, process_id: str) -> List[ProcessStep]:
        """Get all steps for a specific process."""
        process = get_object_or_404(Process, id=process_id, created_by=user)
        return self.process_step_repository.get_by_process(str(process.id))

    def get_process_step(self, user, step_id: str) -> ProcessStep:
        """Get a specific process step."""
        return get_object_or_404(ProcessStep, id=step_id, process__created_by=user)

    def update_process_step(self, user, step_id: str, step_data: Dict[str, Any]) -> ProcessStep:
        """Update an existing process step."""
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        return self.process_step_repository.update(step, **step_data)

    def delete_process_step(self, user, step_id: str) -> bool:
        """Delete a process step."""
        step = get_object_or_404(ProcessStep, id=step_id, process__created_by=user)
        
        deleted_order = step.order_num
        process_id = str(step.process.id)
        
        self.process_step_repository.delete(step)
        self.process_step_repository.reorder_steps_after_delete(process_id, deleted_order)
        
        return True

    def get_process_steps_public(self, process_id: str) -> List[ProcessStep]:
        """Get all steps for a specific process (for public access)."""
        return self.process_step_repository.get_by_process(process_id)

    def get_process_step_by_id(self, step_id: str) -> ProcessStep:
        """Get a process step by ID (for public access)."""
        return self.process_step_repository.get_by_id(step_id)


# =============================================================================
# CATEGORY SERVICE
# =============================================================================

class CategoryService:
    """Service layer for category operations with business logic."""
    
    def __init__(self):
        self.category_repository = CategoryRepository()
    
    def create_category(self, user, category_data: Dict[str, Any]) -> Category:
        """Create a new category."""
        return self.category_repository.create(created_by=user, **category_data)

    def get_user_categories(self, user) -> List[Category]:
        """Get all categories for a specific user."""
        return self.category_repository.get_by_user(str(user.id))

    def get_category(self, user, category_id: str) -> Category:
        """Get a specific category for a user."""
        return get_object_or_404(Category, id=category_id, created_by=user)

    def update_category(self, user, category_id: str, category_data: Dict[str, Any]) -> Category:
        """Update an existing category."""
        category = get_object_or_404(Category, id=category_id, created_by=user)
        return self.category_repository.update(category, **category_data)

    def delete_category(self, user, category_id: str) -> bool:
        """Delete a category."""
        category = get_object_or_404(Category, id=category_id, created_by=user)
        return self.category_repository.delete(category)


class EntityCategoryService:
    """Service layer for entity category operations with business logic."""
    
    def __init__(self):
        self.entity_category_repository = EntityCategoryRepository()
    
    def create_entity_category(self, user, entity_type: str, entity_id: str, category_data: Dict[str, Any]) -> EntityCategory:
        """Create a new entity category association."""
        # Verify user owns the entity
        if entity_type == 'form':
            entity = get_object_or_404(Form, id=entity_id, created_by=user)
        elif entity_type == 'process':
            entity = get_object_or_404(Process, id=entity_id, created_by=user)
        else:
            raise ValidationError("Invalid entity type. Must be 'form' or 'process'.")

        # Verify user owns the category
        category = get_object_or_404(Category, id=category_data['category'].id, created_by=user)

        return self.entity_category_repository.create(
            entity_type=entity_type,
            entity_id=entity_id,
            category=category,
            **category_data
        )

    def get_user_entity_categories(self, user) -> List[EntityCategory]:
        """Get all entity categories for user's entities."""
        return self.entity_category_repository.get_by_user(str(user.id))

    def get_entity_categories(self, user, entity_type: str, entity_id: str) -> List[EntityCategory]:
        """Get all categories for a specific entity."""
        # Verify user owns the entity
        if entity_type == 'form':
            get_object_or_404(Form, id=entity_id, created_by=user)
        elif entity_type == 'process':
            get_object_or_404(Process, id=entity_id, created_by=user)
        else:
            raise ValidationError("Invalid entity type. Must be 'form' or 'process'.")

        return self.entity_category_repository.get_by_entity(entity_type, entity_id)

    def get_entity_category(self, user, entity_category_id: str) -> EntityCategory:
        """Get a specific entity category."""
        return get_object_or_404(EntityCategory, id=entity_category_id, category__created_by=user)

    def update_entity_category(self, user, entity_category_id: str, entity_category_data: Dict[str, Any]) -> EntityCategory:
        """Update an existing entity category."""
        entity_category = get_object_or_404(EntityCategory, id=entity_category_id, category__created_by=user)
        return self.entity_category_repository.update(entity_category, **entity_category_data)

    def delete_entity_category(self, user, entity_category_id: str) -> bool:
        """Delete an entity category."""
        entity_category = get_object_or_404(EntityCategory, id=entity_category_id, category__created_by=user)
        return self.entity_category_repository.delete(entity_category)


# =============================================================================
# RESPONSE SERVICE
# =============================================================================

class ResponseService:
    """Service layer for response operations with business logic."""
    
    def __init__(self):
        self.response_repository = ResponseRepository()
        self.answer_repository = AnswerRepository()
    
    def submit_response(self, form_id: str, answers_data: List[Dict[str, Any]], 
                       ip_address: str = '', user_agent: str = '', submitted_by=None) -> FormResponse:
        """Submit a response to a form."""
        try:
            form = Form.objects.get(id=form_id, is_active=True)
        except Form.DoesNotExist:
            raise ValidationError("Form not found or inactive.")

        if not answers_data:
            raise ValidationError("At least one answer is required.")

        with transaction.atomic():
            # Create the response
            response = self.response_repository.create(
                form=form,
                ip_address=ip_address,
                user_agent=user_agent,
                submitted_by=submitted_by
            )

            # Create answers
            for answer_data in answers_data:
                if not isinstance(answer_data, dict) or 'field_id' not in answer_data or 'value' not in answer_data:
                    raise ValidationError("Each answer must have 'field_id' and 'value'.")

                try:
                    field = Field.objects.get(id=answer_data['field_id'], form=form)
                except Field.DoesNotExist:
                    raise ValidationError("Field must belong to the same form as the response.")

                self.answer_repository.create(
                    response=response,
                    field=field,
                    value=answer_data['value']
                )

        return response

    def get_user_responses(self, user) -> List[FormResponse]:
        """Get all responses for user's forms."""
        return self.response_repository.get_by_user(str(user.id))

    def get_form_responses(self, user, form_id: str) -> List[FormResponse]:
        """Get all responses for a specific form."""
        form = get_object_or_404(Form, id=form_id, created_by=user)
        return self.response_repository.get_by_form(str(form.id))

    def get_response(self, user, response_id: str) -> FormResponse:
        """Get a specific response."""
        return get_object_or_404(FormResponse, id=response_id, form__created_by=user)

    def update_response(self, user, response_id: str, response_data: Dict[str, Any]) -> FormResponse:
        """Update an existing response."""
        response = get_object_or_404(FormResponse, id=response_id, form__created_by=user)
        return self.response_repository.update(response, **response_data)

    def delete_response(self, user, response_id: str) -> bool:
        """Delete a response."""
        response = get_object_or_404(FormResponse, id=response_id, form__created_by=user)
        return self.response_repository.delete(response)


class AnswerService:
    """Service layer for answer operations with business logic."""
    
    def __init__(self):
        self.answer_repository = AnswerRepository()
    
    def create_answer(self, user, response_id: str, field_id: str, value: str) -> Answer:
        """Create a new answer."""
        response = get_object_or_404(FormResponse, id=response_id, form__created_by=user)
        field = get_object_or_404(Field, id=field_id, form=response.form)

        return self.answer_repository.create(
            response=response,
            field=field,
            value=value
        )

    def get_user_answers(self, user) -> List[Answer]:
        """Get all answers for user's responses."""
        return self.answer_repository.get_by_user(str(user.id))

    def get_response_answers(self, user, response_id: str) -> List[Answer]:
        """Get all answers for a specific response."""
        response = get_object_or_404(FormResponse, id=response_id, form__created_by=user)
        return self.answer_repository.get_by_response(str(response.id))

    def get_answer(self, user, answer_id: str) -> Answer:
        """Get a specific answer."""
        return get_object_or_404(Answer, id=answer_id, response__form__created_by=user)

    def update_answer(self, user, answer_id: str, answer_data: Dict[str, Any]) -> Answer:
        """Update an existing answer."""
        answer = get_object_or_404(Answer, id=answer_id, response__form__created_by=user)
        return self.answer_repository.update(answer, **answer_data)

    def delete_answer(self, user, answer_id: str) -> bool:
        """Delete an answer."""
        answer = get_object_or_404(Answer, id=answer_id, response__form__created_by=user)
        return self.answer_repository.delete(answer)
