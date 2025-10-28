from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.http import Http404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view

from forms.models import (
    Field, Form, Process, ProcessStep, Category, EntityCategory, 
    Response as FormResponse, Answer
)
from forms.serializers import (
    # Field serializers
    FieldSerializer, FieldCreateSerializer, FieldUpdateSerializer,
    FieldListSerializer, FieldReorderSerializer,
    # Form serializers
    FormSerializer, FormCreateSerializer, FormUpdateSerializer,
    FormListSerializer, PublicFormSerializer, PublicFormAccessSerializer,
    # Process serializers
    ProcessSerializer, ProcessCreateSerializer, ProcessUpdateSerializer,
    ProcessListSerializer, ProcessStepSerializer, ProcessStepCreateSerializer,
    ProcessStepUpdateSerializer, ProcessStepListSerializer,
    # Category serializers
    CategorySerializer, CategoryCreateSerializer, CategoryUpdateSerializer,
    CategoryListSerializer, EntityCategorySerializer, EntityCategoryCreateSerializer,
    # Response serializers
    ResponseSerializer, ResponseCreateSerializer, ResponseListSerializer,
    AnswerSerializer, AnswerCreateSerializer, AnswerListSerializer
)
from forms.services.services import (
    FieldService, FormService, ProcessService, ProcessStepService,
    CategoryService, EntityCategoryService, ResponseService, AnswerService
)


# =============================================================================
# FIELD VIEWSETS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List Fields",
        description="Get all fields for forms owned by the authenticated user",
        tags=["Form Fields"]
    ),
    create=extend_schema(
        summary="Create Field",
        description="Create a new field for a form",
        tags=["Form Fields"]
    ),
    retrieve=extend_schema(
        summary="Get Field",
        description="Get a specific field by ID",
        tags=["Form Fields"]
    ),
    update=extend_schema(
        summary="Update Field",
        description="Update an existing field",
        tags=["Form Fields"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Field",
        description="Partially update an existing field",
        tags=["Form Fields"]
    ),
    destroy=extend_schema(
        summary="Delete Field",
        description="Delete a field",
        tags=["Form Fields"]
    ),
    by_form=extend_schema(
        summary="Get Fields by Form",
        description="Get all fields for a specific form",
        tags=["Form Fields"]
    ),
    reorder=extend_schema(
        summary="Reorder Field",
        description="Change the order of a field within its form",
        tags=["Form Fields"]
    ),
    field_types=extend_schema(
        summary="Get Field Types",
        description="Get available field types (text, select, checkbox)",
        tags=["Form Fields"]
    ),
    my_fields=extend_schema(
        summary="Get My Fields",
        description="Get all fields for forms owned by the authenticated user",
        tags=["Form Fields"]
    )
)
class FieldViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fields with full CRUD operations and custom actions.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Field.objects.all()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_service = FieldService()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return FieldCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FieldUpdateSerializer
        elif self.action == 'list':
            return FieldListSerializer
        return FieldSerializer
    
    def get_queryset(self):
        """Return fields belonging to the authenticated user's forms."""
        return self.field_service.get_user_fields(self.request.user)
    
    def get_object(self):
        """Get a single field object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        try:
            field = self.field_service.get_field(self.request.user, lookup_value)
            return field
        except Field.DoesNotExist:
            raise Http404("Field not found")
    
    def perform_create(self, serializer):
        """Create a new field using the service layer."""
        form_id = serializer.validated_data['form'].id
        field_data = {
            'label': serializer.validated_data['label'],
            'field_type': serializer.validated_data['field_type'],
            'is_required': serializer.validated_data['is_required'],
            'options': serializer.validated_data.get('options', {}),
            'order_num': serializer.validated_data.get('order_num', 0)
        }
        
        field = self.field_service.create_field(
            user=self.request.user,
            form_id=str(form_id),
            field_data=field_data
        )
        
        serializer.instance = field
    
    def perform_update(self, serializer):
        """Update an existing field using the service layer."""
        field_id = serializer.instance.id
        field_data = {
            'label': serializer.validated_data.get('label', serializer.instance.label),
            'field_type': serializer.validated_data.get('field_type', serializer.instance.field_type),
            'is_required': serializer.validated_data.get('is_required', serializer.instance.is_required),
            'options': serializer.validated_data.get('options', serializer.instance.options),
            'order_num': serializer.validated_data.get('order_num', serializer.instance.order_num)
        }
        
        field_data = {k: v for k, v in field_data.items() if v is not None}
        
        field = self.field_service.update_field(
            user=self.request.user,
            field_id=str(field_id),
            field_data=field_data
        )
        
        serializer.instance = field
    
    def perform_destroy(self, instance):
        """Delete a field using the service layer."""
        self.field_service.delete_field(
            user=self.request.user,
            field_id=str(instance.id)
        )
    
    @action(detail=False, methods=['get'])
    def by_form(self, request):
        """Get all fields for a specific form."""
        form_id = request.query_params.get('form_id')
        if not form_id:
            return Response(
                {'error': 'form_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fields = self.field_service.get_form_fields(
                user=request.user,
                form_id=form_id
            )
            serializer = FieldListSerializer(fields, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Reorder a field within its form."""
        field = self.get_object()
        
        serializer = FieldReorderSerializer(
            data=request.data,
            context={'field': field}
        )
        
        if serializer.is_valid():
            try:
                updated_field = self.field_service.reorder_field(
                    user=request.user,
                    field_id=str(field.id),
                    new_order=serializer.validated_data['new_order']
                )
                
                response_serializer = FieldSerializer(updated_field)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
                
            except ValidationError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def field_types(self, request):
        """Get available field types."""
        field_types = self.field_service.get_field_types()
        return Response(field_types, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_fields(self, request):
        """Get all fields for the authenticated user's forms."""
        return self.list(request)


# =============================================================================
# FORM VIEWSETS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List Forms",
        description="Get all forms owned by the authenticated user",
        tags=["Forms"]
    ),
    create=extend_schema(
        summary="Create Form",
        description="Create a new form",
        tags=["Forms"]
    ),
    retrieve=extend_schema(
        summary="Get Form",
        description="Get a specific form by ID",
        tags=["Forms"]
    ),
    update=extend_schema(
        summary="Update Form",
        description="Update an existing form",
        tags=["Forms"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Form",
        description="Partially update an existing form",
        tags=["Forms"]
    ),
    destroy=extend_schema(
        summary="Delete Form",
        description="Delete a form",
        tags=["Forms"]
    ),
    my_forms=extend_schema(
        summary="List My Forms",
        description="Get all forms created by the authenticated user",
        tags=["Forms"]
    ),
    public_forms=extend_schema(
        summary="List Public Forms (Deprecated)",
        description="Get a list of all public forms. Use /api/v1/forms/public/forms/ instead.",
        tags=["Forms"]
    )
)
class FormViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing forms.
    """
    queryset = Form.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    form_service = FormService()

    def get_queryset(self):
        """Filter forms by the authenticated user."""
        return self.queryset.filter(created_by=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return FormCreateSerializer
        if self.action in ['update', 'partial_update']:
            return FormUpdateSerializer
        if self.action == 'list':
            return FormListSerializer
        return FormSerializer

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        try:
            self.form_service.create_form(self.request.user, serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_update(self, serializer):
        """Update the form."""
        try:
            self.form_service.update_form(self.request.user, str(self.get_object().id), serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete the form."""
        self.form_service.delete_form(self.request.user, str(instance.id))

    @action(detail=False, methods=['get'])
    def my_forms(self, request):
        """Get all forms created by the authenticated user."""
        forms = self.form_service.get_user_forms(request.user)
        serializer = FormListSerializer(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def public_forms(self, request):
        """Get all public forms."""
        try:
            forms = self.form_service.get_public_forms()
            serializer = FormListSerializer(forms, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="List Public Forms",
        description="Get all public forms (no authentication required)",
        tags=["Public Forms"]
    ),
    retrieve=extend_schema(
        summary="Get Public Form",
        description="Get a public form by ID (no authentication required)",
        tags=["Public Forms"]
    ),
    submit_response=extend_schema(
        summary="Submit Response to Public Form",
        description="Submit a response to a public form",
        tags=["Public Forms"]
    )
)
class PublicFormViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for public form access (no authentication required).
    """
    permission_classes = [permissions.AllowAny]
    form_service = FormService()
    response_service = ResponseService()
    queryset = Form.objects.filter(is_public=True, is_active=True)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'submit_response':
            return ResponseCreateSerializer
        return PublicFormSerializer

    def get_object(self):
        """Get a public form by ID."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        form = self.form_service.get_public_form(lookup_value)
        if not form:
            raise Http404("Public form not found")

        # Track the view
        ip_address = self.request.META.get('REMOTE_ADDR', '')
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        self.form_service.track_form_view(form, ip_address, user_agent)

        return form

    @action(detail=True, methods=['post'], serializer_class=ResponseCreateSerializer)
    def submit_response(self, request, pk=None):
        """Submit a response to a public form."""
        form = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            response_instance = self.response_service.submit_response(
                form_id=str(form.id),
                answers_data=serializer.validated_data['answers'],
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                submitted_by=request.user if request.user.is_authenticated else None
            )
            return Response(ResponseSerializer(response_instance).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    validate_access=extend_schema(
        summary="Validate Private Form Access",
        description="Validate access to a private form using a password.",
        request=PublicFormAccessSerializer,
        responses={200: {'description': 'Access granted'}, 401: {'description': 'Access denied'}},
        tags=["Public Forms"]
    )
)
class PrivateFormViewSet(viewsets.GenericViewSet):
    """
    ViewSet for validating private form access.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicFormAccessSerializer
    form_service = FormService()

    @action(detail=False, methods=['post'])
    def validate_access(self, request):
        """Validate access to a private form."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form_id = serializer.validated_data['form_id']
        password = serializer.validated_data['password']

        try:
            form = self.form_service.validate_form_access(str(form_id), password)
            # Track the view if access is granted
            ip_address = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            self.form_service.track_form_view(form, ip_address, user_agent)
            serializer = PublicFormSerializer(form)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# PROCESS VIEWSETS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List Processes",
        description="Get all processes owned by the authenticated user",
        tags=["Processes"]
    ),
    create=extend_schema(
        summary="Create Process",
        description="Create a new process",
        tags=["Processes"]
    ),
    retrieve=extend_schema(
        summary="Get Process",
        description="Get a specific process by ID",
        tags=["Processes"]
    ),
    update=extend_schema(
        summary="Update Process",
        description="Update an existing process",
        tags=["Processes"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Process",
        description="Partially update an existing process",
        tags=["Processes"]
    ),
    destroy=extend_schema(
        summary="Delete Process",
        description="Delete a process",
        tags=["Processes"]
    ),
    my_processes=extend_schema(
        summary="List My Processes",
        description="Get all processes created by the authenticated user",
        tags=["Processes"]
    ),
    public_processes=extend_schema(
        summary="List Public Processes",
        description="Get all public processes",
        tags=["Processes"]
    ),
    process_types=extend_schema(
        summary="Get Process Types",
        description="List available process types (linear, free).",
        tags=["Processes"]
    )
)
class ProcessViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing processes.
    """
    queryset = Process.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    process_service = ProcessService()

    def get_queryset(self):
        """Filter processes by the authenticated user."""
        return self.queryset.filter(created_by=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProcessCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ProcessUpdateSerializer
        if self.action == 'list':
            return ProcessListSerializer
        return ProcessSerializer

    def perform_create(self, serializer):
        """Create a new process."""
        try:
            self.process_service.create_process(self.request.user, serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_update(self, serializer):
        """Update the process."""
        try:
            self.process_service.update_process(self.request.user, str(self.get_object().id), serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete the process."""
        self.process_service.delete_process(self.request.user, str(instance.id))

    @action(detail=False, methods=['get'])
    def my_processes(self, request):
        """Get all processes created by the authenticated user."""
        processes = self.process_service.get_user_processes(request.user)
        serializer = ProcessListSerializer(processes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def public_processes(self, request):
        """Get all public processes."""
        try:
            processes = self.process_service.get_public_processes()
            serializer = ProcessListSerializer(processes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def process_types(self, request):
        """Get available process types."""
        process_types = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Process.PROCESS_TYPES
        ]
        return Response(process_types, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List Process Steps",
        description="Get all process steps for processes owned by the authenticated user",
        tags=["Process Steps"]
    ),
    create=extend_schema(
        summary="Create Process Step",
        description="Create a new process step",
        tags=["Process Steps"]
    ),
    retrieve=extend_schema(
        summary="Get Process Step",
        description="Get a specific process step by ID",
        tags=["Process Steps"]
    ),
    update=extend_schema(
        summary="Update Process Step",
        description="Update an existing process step",
        tags=["Process Steps"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Process Step",
        description="Partially update an existing process step",
        tags=["Process Steps"]
    ),
    destroy=extend_schema(
        summary="Delete Process Step",
        description="Delete a process step",
        tags=["Process Steps"]
    ),
    by_process=extend_schema(
        summary="Get Process Steps by Process",
        description="Get all steps for a specific process",
        tags=["Process Steps"]
    ),
    my_steps=extend_schema(
        summary="List My Process Steps",
        description="Get all process steps for processes owned by the authenticated user",
        tags=["Process Steps"]
    ),
    reorder=extend_schema(
        summary="Reorder Process Step",
        description="Change the order of a process step within its process.",
        tags=["Process Steps"]
    )
)
class ProcessStepViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing process steps.
    """
    queryset = ProcessStep.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    process_step_service = ProcessStepService()

    def get_queryset(self):
        """Filter process steps by the authenticated user's processes."""
        return self.queryset.filter(process__created_by=self.request.user).order_by('process', 'order_num')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProcessStepCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ProcessStepUpdateSerializer
        if self.action == 'list':
            return ProcessStepListSerializer
        return ProcessStepSerializer

    def perform_create(self, serializer):
        """Create a new process step."""
        try:
            self.process_step_service.create_process_step(self.request.user, serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_update(self, serializer):
        """Update the process step."""
        try:
            self.process_step_service.update_process_step(self.request.user, str(self.get_object().id), serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete the process step."""
        self.process_step_service.delete_process_step(self.request.user, str(instance.id))

    @action(detail=False, methods=['get'])
    def by_process(self, request):
        """Get all steps for a specific process."""
        process_id = request.query_params.get('process_id')
        if not process_id:
            return Response(
                {'detail': 'process_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            steps = self.process_step_service.get_process_steps(
                user=request.user,
                process_id=process_id
            )
            serializer = ProcessStepListSerializer(steps, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_steps(self, request):
        """Get all process steps for processes owned by the authenticated user."""
        return self.list(request)

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Reorder a process step within its process."""
        step = self.get_object()
        
        new_order = request.data.get('new_order')
        if not new_order:
            return Response(
                {'detail': 'new_order is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_order = int(new_order)
        except (ValueError, TypeError):
            return Response(
                {'detail': 'new_order must be a valid integer'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            updated_step = self.process_step_service.reorder_step(
                user=request.user,
                step_id=str(step.id),
                new_order=new_order
            )
            
            response_serializer = ProcessStepSerializer(updated_step)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# =============================================================================
# CATEGORY VIEWSETS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List Categories",
        description="Get all categories owned by the authenticated user",
        tags=["Categories"]
    ),
    create=extend_schema(
        summary="Create Category",
        description="Create a new category",
        tags=["Categories"]
    ),
    retrieve=extend_schema(
        summary="Get Category",
        description="Get a specific category by ID",
        tags=["Categories"]
    ),
    update=extend_schema(
        summary="Update Category",
        description="Update an existing category",
        tags=["Categories"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Category",
        description="Partially update an existing category",
        tags=["Categories"]
    ),
    destroy=extend_schema(
        summary="Delete Category",
        description="Delete a category",
        tags=["Categories"]
    ),
    my_categories=extend_schema(
        summary="List My Categories",
        description="Get all categories created by the authenticated user",
        tags=["Categories"]
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories.
    """
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    category_service = CategoryService()

    def get_queryset(self):
        """Filter categories by the authenticated user."""
        return self.queryset.filter(created_by=self.request.user).order_by('created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CategoryCreateSerializer
        if self.action in ['update', 'partial_update']:
            return CategoryUpdateSerializer
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer

    def perform_create(self, serializer):
        """Create a new category."""
        try:
            self.category_service.create_category(self.request.user, serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError({'detail': str(e)})

    def perform_update(self, serializer):
        """Update the category."""
        try:
            self.category_service.update_category(self.request.user, str(self.get_object().id), serializer.validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete the category."""
        try:
            self.category_service.delete_category(self.request.user, str(instance.id))
        except ValidationError as e:
            raise serializers.ValidationError({'detail': str(e)})

    @action(detail=False, methods=['get'])
    def my_categories(self, request):
        """Get all categories created by the authenticated user."""
        return self.list(request)


@extend_schema_view(
    list=extend_schema(
        summary="List Entity Categories",
        description="Get all entity categories for entities owned by the authenticated user",
        tags=["Entity Categories"]
    ),
    create=extend_schema(
        summary="Create Entity Category",
        description="Create a new entity category association",
        tags=["Entity Categories"]
    ),
    retrieve=extend_schema(
        summary="Get Entity Category",
        description="Get a specific entity category by ID",
        tags=["Entity Categories"]
    ),
    update=extend_schema(
        summary="Update Entity Category",
        description="Update an existing entity category",
        tags=["Entity Categories"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Entity Category",
        description="Partially update an existing entity category",
        tags=["Entity Categories"]
    ),
    destroy=extend_schema(
        summary="Delete Entity Category",
        description="Delete an entity category",
        tags=["Entity Categories"]
    ),
    by_entity=extend_schema(
        summary="Get Entity Categories by Entity",
        description="Get all categories for a specific entity",
        tags=["Entity Categories"]
    ),
    my_entity_categories=extend_schema(
        summary="List My Entity Categories",
        description="Get all entity categories for entities owned by the authenticated user",
        tags=["Entity Categories"]
    )
)
class EntityCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing entity categories.
    """
    queryset = EntityCategory.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    entity_category_service = EntityCategoryService()

    def get_queryset(self):
        """Filter entity categories by the authenticated user's entities."""
        return self.queryset.filter(
            Q(entity_type='form', entity_id__in=Form.objects.filter(created_by=self.request.user).values_list('id', flat=True)) |
            Q(entity_type='process', entity_id__in=Process.objects.filter(created_by=self.request.user).values_list('id', flat=True))
        ).order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return EntityCategoryCreateSerializer
        if self.action in ['update', 'partial_update']:
            return EntityCategorySerializer
        if self.action == 'list':
            return EntityCategorySerializer
        return EntityCategorySerializer

    def perform_create(self, serializer):
        """Create a new entity category."""
        try:
            entity_type = serializer.validated_data.get('entity_type', 'form')
            entity_id = serializer.validated_data.get('entity_id')
            category_data = serializer.validated_data
            
            self.entity_category_service.create_entity_category(
                self.request.user, 
                entity_type, 
                entity_id, 
                category_data
            )
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_update(self, serializer):
        """Update the entity category."""
        try:
            self.entity_category_service.update_entity_category(
                self.request.user, 
                str(self.get_object().id), 
                serializer.validated_data
            )
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete the entity category."""
        self.entity_category_service.delete_entity_category(self.request.user, str(instance.id))

    @action(detail=False, methods=['get'])
    def by_entity(self, request):
        """Get all categories for a specific entity."""
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')
        
        if not entity_type or not entity_id:
            return Response(
                {'detail': 'entity_type and entity_id parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            entity_categories = self.entity_category_service.get_entity_categories(
                user=request.user,
                entity_type=entity_type,
                entity_id=entity_id
            )
            serializer = EntityCategorySerializer(entity_categories, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_entity_categories(self, request):
        """Get all entity categories for entities owned by the authenticated user."""
        return self.list(request)


# =============================================================================
# RESPONSE VIEWSETS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List Responses",
        description="Get all responses for forms owned by the authenticated user",
        tags=["Form Responses"]
    ),
    create=extend_schema(
        summary="Create Response",
        description="Create a new response for a form",
        tags=["Form Responses"]
    ),
    retrieve=extend_schema(
        summary="Get Response",
        description="Get a specific response by ID",
        tags=["Form Responses"]
    ),
    update=extend_schema(
        summary="Update Response",
        description="Update an existing response",
        tags=["Form Responses"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Response",
        description="Partially update an existing response",
        tags=["Form Responses"]
    ),
    destroy=extend_schema(
        summary="Delete Response",
        description="Delete a response",
        tags=["Form Responses"]
    ),
    by_form=extend_schema(
        summary="Get Responses by Form",
        description="Get all responses for a specific form",
        tags=["Form Responses"]
    ),
    my_responses=extend_schema(
        summary="List My Responses",
        description="Get all responses for forms owned by the authenticated user",
        tags=["Form Responses"]
    )
)
class ResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing responses.
    """
    queryset = FormResponse.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    response_service = ResponseService()

    def get_queryset(self):
        """Filter responses by the authenticated user's forms."""
        return self.queryset.filter(form__created_by=self.request.user).order_by('-submitted_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ResponseCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ResponseSerializer
        if self.action == 'list':
            return ResponseListSerializer
        return ResponseSerializer

    def perform_create(self, serializer):
        """Create a new response."""
        try:
            self.response_service.submit_response(
                form_id=str(serializer.validated_data['form'].id),
                answers_data=serializer.validated_data['answers'],
                ip_address=self.request.META.get('REMOTE_ADDR', ''),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                submitted_by=self.request.user
            )
        except ValidationError as e:
            raise serializers.ValidationError({'detail': str(e)})

    def perform_update(self, serializer):
        """Update the response."""
        try:
            self.response_service.update_response(
                self.request.user, 
                str(self.get_object().id), 
                serializer.validated_data
            )
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete the response."""
        self.response_service.delete_response(self.request.user, str(instance.id))

    @action(detail=False, methods=['get'])
    def by_form(self, request):
        """Get all responses for a specific form."""
        form_id = request.query_params.get('form_id')
        if not form_id:
            return Response(
                {'detail': 'form_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            responses = self.response_service.get_form_responses(
                user=request.user,
                form_id=form_id
            )
            serializer = ResponseListSerializer(responses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_responses(self, request):
        """Get all responses for forms owned by the authenticated user."""
        return self.list(request)


@extend_schema_view(
    list=extend_schema(
        summary="List Answers",
        description="Get all answers for responses owned by the authenticated user",
        tags=["Form Answers"]
    ),
    create=extend_schema(
        summary="Create Answer",
        description="Create a new answer for a response",
        tags=["Form Answers"]
    ),
    retrieve=extend_schema(
        summary="Get Answer",
        description="Get a specific answer by ID",
        tags=["Form Answers"]
    ),
    update=extend_schema(
        summary="Update Answer",
        description="Update an existing answer",
        tags=["Form Answers"]
    ),
    partial_update=extend_schema(
        summary="Partial Update Answer",
        description="Partially update an existing answer",
        tags=["Form Answers"]
    ),
    destroy=extend_schema(
        summary="Delete Answer",
        description="Delete an answer",
        tags=["Form Answers"]
    ),
    by_response=extend_schema(
        summary="Get Answers by Response",
        description="Get all answers for a specific response",
        tags=["Form Answers"]
    ),
    my_answers=extend_schema(
        summary="List My Answers",
        description="Get all answers for responses owned by the authenticated user",
        tags=["Form Answers"]
    ),
    by_field=extend_schema(
        summary="Get Answers by Field",
        description="Get all answers submitted for a specific field.",
        tags=["Form Answers"]
    ),
    field_statistics=extend_schema(
        summary="Get Field Statistics",
        description="Get aggregated statistics for a specific field (counts, common values, timeline).",
        tags=["Form Answers"]
    )
)
class AnswerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing answers.
    """
    queryset = Answer.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    answer_service = AnswerService()

    def get_queryset(self):
        """Filter answers by the authenticated user's responses."""
        return self.queryset.filter(response__form__created_by=self.request.user).order_by('-response__submitted_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return AnswerCreateSerializer
        if self.action in ['update', 'partial_update']:
            return AnswerSerializer
        if self.action == 'list':
            return AnswerListSerializer
        return AnswerSerializer

    def perform_create(self, serializer):
        """Create a new answer."""
        try:
            self.answer_service.create_answer(
                user=self.request.user,
                response_id=str(serializer.validated_data['response'].id),
                field_id=str(serializer.validated_data['field'].id),
                value=serializer.validated_data['value']
            )
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_update(self, serializer):
        """Update the answer."""
        try:
            self.answer_service.update_answer(
                self.request.user, 
                str(self.get_object().id), 
                serializer.validated_data
            )
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def perform_destroy(self, instance):
        """Delete the answer."""
        self.answer_service.delete_answer(self.request.user, str(instance.id))

    @action(detail=False, methods=['get'])
    def by_response(self, request):
        """Get all answers for a specific response."""
        response_id = request.query_params.get('response_id')
        if not response_id:
            return Response(
                {'detail': 'response_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            answers = self.answer_service.get_response_answers(
                user=request.user,
                response_id=response_id
            )
            serializer = AnswerListSerializer(answers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_answers(self, request):
        """Get all answers for responses owned by the authenticated user."""
        return self.list(request)

    @action(detail=False, methods=['get'])
    def by_field(self, request):
        """Get all answers for a specific field."""
        field_id = request.query_params.get('field_id')
        if not field_id:
            return Response(
                {'detail': 'field_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            answers = self.answer_service.get_field_answers(
                user=request.user,
                field_id=field_id
            )
            serializer = AnswerListSerializer(answers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def field_statistics(self, request):
        """Get statistics for a specific field."""
        field_id = request.query_params.get('field_id')
        if not field_id:
            return Response(
                {'detail': 'field_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            statistics = self.answer_service.get_field_statistics(
                user=request.user,
                field_id=field_id
            )
            return Response(statistics, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# PROCESS WORKFLOW VIEWSETS
# =============================================================================

@extend_schema_view(
    get_process_steps=extend_schema(
        summary="Get Process Steps",
        description="Get all steps for a given process.",
        tags=["Process Workflow"]
    ),
    get_current_step=extend_schema(
        summary="Get Current Process Step",
        description="Get the current step for a linear process, considering completed steps.",
        tags=["Process Workflow"]
    ),
    complete_step=extend_schema(
        summary="Complete Process Step",
        description="Submit a response to the form associated with a process step.",
        request=ResponseCreateSerializer,
        responses={201: ResponseSerializer, 400: {'description': 'Bad Request'}},
        tags=["Process Workflow"]
    ),
    get_process_progress=extend_schema(
        summary="Get Process Progress",
        description="Get the overall progress for a process, including completed steps.",
        tags=["Process Workflow"]
    )
)
class ProcessWorkflowViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing process workflows and form completion.
    """
    permission_classes = [permissions.AllowAny] # Public access for workflow
    process_service = ProcessService()
    process_step_service = ProcessStepService()
    form_service = FormService()
    response_service = ResponseService()

    @action(detail=False, methods=['get'])
    def get_process_steps(self, request):
        """Get all steps for a given process."""
        process_id = request.query_params.get('process_id')
        if not process_id:
            return Response({'detail': 'process_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            process = self.process_service.get_process_by_id(process_id)
            if not process:
                raise Http404("Process not found")

            steps = self.process_step_service.get_process_steps_public(process_id)
            serializer = ProcessStepSerializer(steps, many=True)
            return Response({
                'process': ProcessSerializer(process).data,
                'steps': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_current_step(self, request):
        """Get the current step for a linear process, considering completed steps."""
        process_id = request.query_params.get('process_id')
        if not process_id:
            return Response({'detail': 'process_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            process = self.process_service.get_process_by_id(process_id)
            if not process:
                raise Http404("Process not found")

            if process.process_type != 'linear':
                return Response(
                    {'detail': 'This action is only for linear processes.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            steps = self.process_step_service.get_process_steps_public(process_id)
            current_step = None
            for step in steps:
                if not self._is_step_completed(step):
                    current_step = step
                    break

            if current_step:
                form = self.form_service.get_public_form(str(current_step.form.id))
                return Response({
                    'current_step': ProcessStepSerializer(current_step).data,
                    'form': PublicFormSerializer(form).data,
                    'is_completed': False
                }, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'All steps completed'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def complete_step(self, request):
        """Complete a process step by submitting the form."""
        try:
            step_id = request.data.get('step_id')
            answers_data = request.data.get('answers', [])

            if not step_id:
                return Response(
                    {'detail': 'step_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the process step
            step = self.process_step_service.get_process_step_by_id(step_id)
            if not step:
                return Response(
                    {'detail': 'Process step not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check access to the process
            process = step.process
            if not process.is_public:
                password = request.data.get('password')
                if not password or not self.process_service.validate_process_access(str(process.id), password):
                    return Response(
                        {'detail': 'This process requires a password'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

            # Submit the response
            ip_address = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Enforce required fields at submission time; ResponseService already validates
            response = self.response_service.submit_response(
                form_id=str(step.form.id),
                answers_data=answers_data,
                ip_address=ip_address,
                user_agent=user_agent,
                submitted_by=None  # Anonymous submission
            )
            return Response({'response': ResponseSerializer(response).data}, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_process_progress(self, request):
        """Get the overall progress for a process, including completed steps."""
        process_id = request.query_params.get('process_id')
        if not process_id:
            return Response({'detail': 'process_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            process = self.process_service.get_process_by_id(process_id)
            if not process:
                raise Http404("Process not found")

            steps = self.process_step_service.get_process_steps_public(process_id)
            total_steps = len(steps)
            completed_steps = sum(1 for step in steps if self._is_step_completed(step))
            is_complete = self._is_process_complete(process)

            return Response({
                'process': ProcessSerializer(process).data,
                'progress': {
                    'total_steps': total_steps,
                    'completed_steps': completed_steps,
                    'progress_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 0,
                    'is_complete': is_complete
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _is_step_completed(self, step):
        """Check if a process step has been completed."""
        # For now, we'll use a simple check - any response to the form means the step is completed
        # In a more complex system, you might want to track step-specific completion
        return FormResponse.objects.filter(form=step.form).exists()

    def _get_next_step(self, process, current_step):
        """Get the next step in a linear process."""
        steps = self.process_step_service.get_process_steps_public(str(process.id))
        for i, step in enumerate(steps):
            if step.id == current_step.id and i + 1 < len(steps):
                return steps[i + 1]
        return None

    def _is_process_complete(self, process):
        """Check if all steps in a process are completed."""
        steps = self.process_step_service.get_process_steps_public(str(process.id))
        return all(self._is_step_completed(step) for step in steps)
