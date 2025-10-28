from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from forms.models import Process, ProcessStep
from forms.serializers import (
    ProcessSerializer, ProcessCreateSerializer, ProcessUpdateSerializer,
    ProcessListSerializer, ProcessStepSerializer, ProcessStepCreateSerializer,
    ProcessStepUpdateSerializer, ProcessStepListSerializer, ProcessStepReorderSerializer
)
from forms.services.process_service import ProcessService, ProcessStepService
from forms.repositories.process_repository import ProcessRepository


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
    process_types=extend_schema(
        summary="Get Process Types",
        description="Get available process types (linear, free)",
        tags=["Processes"]
    ),
    my_processes=extend_schema(
        summary="Get My Processes",
        description="Get all processes owned by the authenticated user",
        tags=["Processes"]
    ),
    public_processes=extend_schema(
        summary="Get Public Processes",
        description="Get all public processes",
        tags=["Processes"]
    )
)
class ProcessViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing processes with full CRUD operations and custom actions.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Process.objects.all()  # For DRF Spectacular discovery
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_service = ProcessService()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProcessCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProcessUpdateSerializer
        elif self.action == 'list':
            return ProcessListSerializer
        return ProcessSerializer
    
    def get_queryset(self):
        """Return processes belonging to the authenticated user."""
        return self.process_service.get_user_processes(self.request.user)
    
    def get_object(self):
        """Get a single process object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        # Use the repository to get the process
        process_repo = ProcessRepository()
        
        try:
            process = process_repo.get_by_id(lookup_value)
            if not process or process.created_by != self.request.user:
                raise Http404("Process not found")
            return process
        except Process.DoesNotExist:
            raise Http404("Process not found")
    
    def perform_create(self, serializer):
        """Create a new process using the service layer."""
        process_data = serializer.validated_data
        
        try:
            process = self.process_service.create_process(self.request.user, process_data)
            serializer.instance = process
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_update(self, serializer):
        """Update an existing process using the service layer."""
        process_id = self.kwargs.get(self.lookup_field)
        process_data = serializer.validated_data
        
        try:
            process = self.process_service.update_process(self.request.user, process_id, process_data)
            serializer.instance = process
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_destroy(self, instance):
        """Delete a process using the service layer."""
        try:
            self.process_service.delete_process(self.request.user, str(instance.id))
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['get'], url_path='process_types')
    def process_types(self, request):
        """Get available process types."""
        process_types = self.process_service.get_process_types()
        return Response(process_types, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='my_processes')
    def my_processes(self, request):
        """Get all processes for the authenticated user."""
        processes = self.process_service.get_user_processes(request.user)
        serializer = ProcessListSerializer(processes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='public_processes')
    def public_processes(self, request):
        """Get all public processes."""
        processes = self.process_service.get_public_processes()
        serializer = ProcessListSerializer(processes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        summary="Get Steps by Process",
        description="Get all steps for a specific process",
        tags=["Process Steps"]
    ),
    reorder=extend_schema(
        summary="Reorder Process Step",
        description="Change the order of a process step within its process",
        tags=["Process Steps"]
    ),
    my_steps=extend_schema(
        summary="Get My Process Steps",
        description="Get all process steps for processes owned by the authenticated user",
        tags=["Process Steps"]
    )
)
class ProcessStepViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing process steps with full CRUD operations and custom actions.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProcessStep.objects.all()  # For DRF Spectacular discovery
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_step_service = ProcessStepService()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProcessStepCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProcessStepUpdateSerializer
        elif self.action == 'list':
            return ProcessStepListSerializer
        return ProcessStepSerializer
    
    def get_queryset(self):
        """Return process steps belonging to the authenticated user's processes."""
        return self.process_step_service.get_user_process_steps(self.request.user)
    
    def get_object(self):
        """Get a single process step object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        # Use the repository to get the process step
        from forms.repositories.process_repository import ProcessStepRepository
        step_repo = ProcessStepRepository()
        
        try:
            step = step_repo.get_by_id(lookup_value)
            if not step or step.process.created_by != self.request.user:
                raise Http404("Process step not found")
            return step
        except ProcessStep.DoesNotExist:
            raise Http404("Process step not found")
    
    def perform_create(self, serializer):
        """Create a new process step using the service layer."""
        process_id = serializer.validated_data['process'].id
        step_data = {
            'form': serializer.validated_data['form'],
            'step_name': serializer.validated_data['step_name'],
            'step_description': serializer.validated_data.get('step_description', ''),
            'order_num': serializer.validated_data.get('order_num', 0),
            'is_required': serializer.validated_data.get('is_required', True)
        }
        
        try:
            step = self.process_step_service.create_process_step(self.request.user, str(process_id), step_data)
            serializer.instance = step
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_update(self, serializer):
        """Update an existing process step using the service layer."""
        step_id = self.kwargs.get(self.lookup_field)
        step_data = serializer.validated_data
        
        try:
            step = self.process_step_service.update_process_step(self.request.user, step_id, step_data)
            serializer.instance = step
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_destroy(self, instance):
        """Delete a process step using the service layer."""
        try:
            self.process_step_service.delete_process_step(self.request.user, str(instance.id))
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['get'], url_path='by_process')
    def by_process(self, request):
        """Get steps for a specific process."""
        process_id = request.query_params.get('process_id')
        if not process_id:
            return Response({'detail': 'process_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            steps = self.process_step_service.get_process_steps(request.user, process_id)
            serializer = ProcessStepListSerializer(steps, many=True)
            return Response(serializer.data)
        except (Http404, ValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Reorder a process step within its process."""
        serializer = ProcessStepReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_order = serializer.validated_data['new_order']
        
        try:
            step = self.process_step_service.reorder_process_step(request.user, pk, new_order)
            return Response(ProcessStepSerializer(step).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my_steps')
    def my_steps(self, request):
        """Get all process steps for processes owned by the authenticated user."""
        steps = self.process_step_service.get_user_process_steps(request.user)
        serializer = ProcessStepListSerializer(steps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
