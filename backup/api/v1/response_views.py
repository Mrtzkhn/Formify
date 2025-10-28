from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from django.core.exceptions import ValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from forms.models import Response, Answer
from forms.serializers import (
    ResponseSerializer, ResponseCreateSerializer, ResponseListSerializer,
    AnswerSerializer, AnswerCreateSerializer, AnswerListSerializer
)
from forms.services.response_service import ResponseService, AnswerService


@extend_schema_view(
    list=extend_schema(
        summary="List Responses",
        description="Get all responses for forms owned by the authenticated user",
        tags=["Form Responses"]
    ),
    create=extend_schema(
        summary="Submit Response",
        description="Submit a response to a form",
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
        summary="Get My Responses",
        description="Get all responses submitted by the authenticated user",
        tags=["Form Responses"]
    ),
    form_owner_responses=extend_schema(
        summary="Get Form Owner Responses",
        description="Get all responses for forms owned by the authenticated user",
        tags=["Form Responses"]
    )
)
class ResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing form responses with CRUD operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    response_service = ResponseService()
    queryset = Response.objects.all()  # For DRF Spectacular discovery

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ResponseCreateSerializer
        elif self.action == 'list':
            return ResponseListSerializer
        return ResponseSerializer

    def get_queryset(self):
        """Return responses for forms owned by the authenticated user."""
        return self.response_service.get_form_owner_responses(self.request.user)

    def get_object(self):
        """Get a single response object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        try:
            return self.response_service.get_response_details(self.request.user, lookup_value)
        except ValidationError as e:
            raise Http404(str(e))

    def perform_create(self, serializer):
        """Create a new response using the service layer."""
        form_id = str(serializer.validated_data['form'].id)
        answers_data = serializer.validated_data['answers']
        
        # Get IP address and user agent from request
        ip_address = self.get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        try:
            response = self.response_service.submit_response(
                form_id=form_id,
                answers_data=answers_data,
                ip_address=ip_address,
                user_agent=user_agent,
                submitted_by=self.request.user if self.request.user.is_authenticated else None
            )
            serializer.instance = response
        except ValidationError as e:
            from rest_framework.serializers import ValidationError as DRFValidationError
            raise DRFValidationError({'detail': str(e)})

    def perform_destroy(self, instance):
        """Delete a response using the service layer."""
        try:
            self.response_service.delete_response(self.request.user, str(instance.id))
        except ValidationError as e:
            return DRFResponse({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self):
        """Get client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=False, methods=['get'], url_path='by_form')
    def by_form(self, request):
        """Get responses for a specific form."""
        form_id = request.query_params.get('form_id')
        if not form_id:
            return DRFResponse(
                {'detail': 'form_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            responses = self.response_service.get_form_responses(request.user, form_id)
            serializer = ResponseListSerializer(responses, many=True)
            return DRFResponse(serializer.data)
        except ValidationError as e:
            return DRFResponse({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='my_responses')
    def my_responses(self, request):
        """Get all responses submitted by the authenticated user."""
        responses = self.response_service.get_user_responses(request.user)
        serializer = ResponseListSerializer(responses, many=True)
        return DRFResponse(serializer.data)

    @action(detail=False, methods=['get'], url_path='form_owner_responses')
    def form_owner_responses(self, request):
        """Get all responses for forms owned by the authenticated user."""
        responses = self.response_service.get_form_owner_responses(request.user)
        serializer = ResponseListSerializer(responses, many=True)
        return DRFResponse(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List Answers",
        description="Get all answers for responses accessible by the authenticated user",
        tags=["Form Answers"]
    ),
    create=extend_schema(
        summary="Create Answer",
        description="Create a new answer",
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
    by_field=extend_schema(
        summary="Get Answers by Field",
        description="Get all answers for a specific field",
        tags=["Form Answers"]
    ),
    field_statistics=extend_schema(
        summary="Get Field Statistics",
        description="Get statistics for a specific field",
        tags=["Form Answers"]
    )
)
class AnswerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing form answers.
    """
    permission_classes = [permissions.IsAuthenticated]
    answer_service = AnswerService()
    queryset = Answer.objects.all()  # For DRF Spectacular discovery

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return AnswerCreateSerializer
        elif self.action == 'list':
            return AnswerListSerializer
        return AnswerSerializer

    def get_queryset(self):
        """Return answers accessible by the authenticated user."""
        # This is a simplified queryset - in practice, you'd want to filter
        # based on user permissions
        return Answer.objects.select_related('response', 'field').all()

    def get_object(self):
        """Get a single answer object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        try:
            return Answer.objects.get(id=lookup_value)
        except Answer.DoesNotExist:
            raise Http404("Answer not found")

    @action(detail=False, methods=['get'], url_path='by_response')
    def by_response(self, request):
        """Get answers for a specific response."""
        response_id = request.query_params.get('response_id')
        if not response_id:
            return DRFResponse(
                {'detail': 'response_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            answers = self.answer_service.get_response_answers(request.user, response_id)
            serializer = AnswerListSerializer(answers, many=True)
            return DRFResponse(serializer.data)
        except ValidationError as e:
            return DRFResponse({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by_field')
    def by_field(self, request):
        """Get answers for a specific field."""
        field_id = request.query_params.get('field_id')
        if not field_id:
            return DRFResponse(
                {'detail': 'field_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            answers = self.answer_service.get_field_answers(request.user, field_id)
            serializer = AnswerListSerializer(answers, many=True)
            return DRFResponse(serializer.data)
        except ValidationError as e:
            return DRFResponse({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='field_statistics')
    def field_statistics(self, request):
        """Get statistics for a specific field."""
        field_id = request.query_params.get('field_id')
        if not field_id:
            return DRFResponse(
                {'detail': 'field_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            statistics = self.answer_service.get_field_statistics(request.user, field_id)
            return DRFResponse(statistics)
        except ValidationError as e:
            return DRFResponse({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
