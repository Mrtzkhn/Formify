from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from forms.models import Field, Form
from forms.serializers import (
    FieldSerializer, FieldCreateSerializer, FieldUpdateSerializer,
    FieldListSerializer, FieldReorderSerializer
)
from forms.services.services import FieldService


class FieldViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fields with full CRUD operations and custom actions.
    """
    permission_classes = [permissions.IsAuthenticated]
    
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
        return Field.objects.filter(form__created_by=self.request.user).order_by('form', 'order_num')
    
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
        
        field = FieldService.create_field(
            user=self.request.user,
            form_id=str(form_id),
            field_data=field_data
        )
        
        # Update the serializer instance with the created field
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
        
        # Remove None values
        field_data = {k: v for k, v in field_data.items() if v is not None}
        
        field = FieldService.update_field(
            user=self.request.user,
            field_id=str(field_id),
            field_data=field_data
        )
        
        # Update the serializer instance
        serializer.instance = field
    
    def perform_destroy(self, instance):
        """Delete a field using the service layer."""
        FieldService.delete_field(
            user=self.request.user,
            field_id=str(instance.id)
        )
    
    @action(detail=False, methods=['get'])
    def by_form(self, request):
        """
        Get all fields for a specific form.
        
        Query parameters:
        - form_id: UUID of the form
        """
        form_id = request.query_params.get('form_id')
        if not form_id:
            return Response(
                {'error': 'form_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fields = FieldService.get_form_fields(
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
        """
        Reorder a field within its form.
        
        Request body:
        - new_order: New order number for the field
        """
        field = self.get_object()
        
        serializer = FieldReorderSerializer(
            data=request.data,
            context={'field': field}
        )
        
        if serializer.is_valid():
            try:
                updated_field = FieldService.reorder_field(
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
        """
        Get available field types.
        """
        field_types = FieldService.get_field_types()
        return Response(field_types, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_fields(self, request):
        """
        Get all fields for the authenticated user's forms.
        This is an alias for the list action but with a more descriptive name.
        """
        return self.list(request)
