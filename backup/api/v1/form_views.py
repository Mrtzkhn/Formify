from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from forms.models import Form
from forms.serializers import (
    FormSerializer, FormCreateSerializer, FormUpdateSerializer,
    FormListSerializer, PublicFormSerializer
)
from forms.services.form_service import FormService


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
        summary="Get My Forms",
        description="Get all forms owned by the authenticated user",
        tags=["Forms"]
    ),
    public_forms=extend_schema(
        summary="Get Public Forms",
        description="Get all public forms",
        tags=["Forms"]
    )
)
class FormViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing forms with full CRUD operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    form_service = FormService()
    queryset = Form.objects.all()  # For DRF Spectacular discovery

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return FormCreateSerializer
        elif self.action == 'list':
            return FormListSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return FormUpdateSerializer
        return FormSerializer

    def get_queryset(self):
        """Return forms for the authenticated user."""
        return self.form_service.get_user_forms(self.request.user)

    def get_object(self):
        """Get a single form object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        try:
            return self.form_service.get_form(self.request.user, lookup_value)
        except Form.DoesNotExist:
            raise Http404("Form not found")
    
    def perform_create(self, serializer):
        """Create a new form using the service layer."""
        form_data = {
            'title': serializer.validated_data['title'],
            'description': serializer.validated_data.get('description', ''),
            'is_public': serializer.validated_data.get('is_public', True),
            'access_password': serializer.validated_data.get('access_password', ''),
            'is_active': serializer.validated_data.get('is_active', True)
        }

        form = self.form_service.create_form(
            user=self.request.user,
            form_data=form_data
        )

        # Update the serializer instance with the created form
        serializer.instance = form
    
    def perform_update(self, serializer):
        """Update an existing form using the service layer."""
        form_id = serializer.instance.id
        form_data = {
            'title': serializer.validated_data.get('title', serializer.instance.title),
            'description': serializer.validated_data.get('description', serializer.instance.description),
            'is_public': serializer.validated_data.get('is_public', serializer.instance.is_public),
            'access_password': serializer.validated_data.get('access_password', serializer.instance.access_password),
            'is_active': serializer.validated_data.get('is_active', serializer.instance.is_active)
        }

        # Remove None values
        form_data = {k: v for k, v in form_data.items() if v is not None}

        form = self.form_service.update_form(
            user=self.request.user,
            form_id=str(form_id),
            form_data=form_data
        )

        # Update the serializer instance
        serializer.instance = form
    
    def perform_destroy(self, instance):
        """Delete a form using the service layer."""
        self.form_service.delete_form(
            user=self.request.user,
            form_id=str(instance.id)
        )

    @action(detail=False, methods=['get'])
    def my_forms(self, request):
        """Get all forms owned by the authenticated user."""
        try:
            forms = self.form_service.get_user_forms(request.user)
            serializer = FormListSerializer(forms, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
    queryset = Form.objects.filter(is_public=True, is_active=True)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'submit_response':
            from forms.serializers import ResponseCreateSerializer
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

    @action(detail=True, methods=['post'])
    def submit_response(self, request, pk=None):
        """Submit a response to a public form."""
        try:
            form = self.get_object()
            
            # Use the existing response submission logic
            from forms.services.response_service import ResponseService
            response_service = ResponseService()
            
            ip_address = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            response = response_service.submit_response(
                form_id=str(form.id),
                answers_data=request.data.get('answers', []),
                ip_address=ip_address,
                user_agent=user_agent,
                submitted_by=None  # Anonymous submission
            )
            
            serializer = self.get_serializer(response)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    validate_access=extend_schema(
        summary="Validate Private Form Access",
        description="Validate access to a private form with password",
        tags=["Private Forms"]
    )
)
class PrivateFormViewSet(viewsets.ViewSet):
    """
    ViewSet for private form access with password validation.
    """
    permission_classes = [permissions.AllowAny]
    form_service = FormService()

    @action(detail=False, methods=['post'])
    def validate_access(self, request):
        """Validate access to a private form with password."""
        try:
            form_id = request.data.get('form_id')
            password = request.data.get('password')
            
            if not form_id:
                return Response(
                    {'detail': 'form_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            form = self.form_service.validate_form_access(form_id, password)
            
            # Track the view
            ip_address = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            self.form_service.track_form_view(form, ip_address, user_agent)
            
            serializer = PublicFormSerializer(form)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
