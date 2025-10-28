from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from forms.models import Category, EntityCategory
from forms.serializers import (
    CategorySerializer, CategoryCreateSerializer, CategoryUpdateSerializer,
    CategoryListSerializer, EntityCategorySerializer, EntityCategoryCreateSerializer
)
from forms.services.category_service import CategoryService, EntityCategoryService


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
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories with full CRUD operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    category_service = CategoryService()
    queryset = Category.objects.all()  # For DRF Spectacular discovery

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CategoryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CategoryUpdateSerializer
        elif self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer

    def get_queryset(self):
        """Return categories belonging to the authenticated user."""
        return self.category_service.get_user_categories(self.request.user)

    def get_object(self):
        """Get a single category object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        try:
            return self.category_service.get_category(self.request.user, lookup_value)
        except ValidationError as e:
            raise Http404(str(e))

    def perform_create(self, serializer):
        """Create a new category using the service layer."""
        category_data = serializer.validated_data
        
        try:
            category = self.category_service.create_category(self.request.user, category_data)
            serializer.instance = category
        except ValidationError as e:
            from rest_framework.serializers import ValidationError as DRFValidationError
            raise DRFValidationError({'detail': str(e)})

    def perform_update(self, serializer):
        """Update an existing category using the service layer."""
        category_id = self.kwargs.get(self.lookup_field)
        category_data = serializer.validated_data
        
        try:
            category = self.category_service.update_category(self.request.user, category_id, category_data)
            serializer.instance = category
        except ValidationError as e:
            from rest_framework.serializers import ValidationError as DRFValidationError
            raise DRFValidationError({'detail': str(e)})

    def perform_destroy(self, instance):
        """Delete a category using the service layer."""
        try:
            self.category_service.delete_category(self.request.user, str(instance.id))
        except ValidationError as e:
            from rest_framework.serializers import ValidationError as DRFValidationError
            raise DRFValidationError({'detail': str(e)})


@extend_schema_view(
    list=extend_schema(
        summary="List Entity Categories",
        description="Get all entity category associations for the authenticated user",
        tags=["Entity Categories"]
    ),
    create=extend_schema(
        summary="Create Entity Category",
        description="Link an entity to a category",
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
        description="Unlink an entity from a category",
        tags=["Entity Categories"]
    ),
    by_entity=extend_schema(
        summary="Get Categories by Entity",
        description="Get all categories for a specific entity",
        tags=["Entity Categories"]
    )
)
class EntityCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing entity category associations.
    """
    permission_classes = [permissions.IsAuthenticated]
    entity_category_service = EntityCategoryService()
    queryset = EntityCategory.objects.all()  # For DRF Spectacular discovery

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return EntityCategoryCreateSerializer
        return EntityCategorySerializer

    def get_queryset(self):
        """Return entity categories for the authenticated user."""
        return self.entity_category_service.get_user_entity_categories(self.request.user)

    def get_object(self):
        """Get a single entity category object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        try:
            return EntityCategory.objects.get(id=lookup_value)
        except EntityCategory.DoesNotExist:
            raise Http404("Entity category not found")

    def perform_create(self, serializer):
        """Create a new entity category using the service layer."""
        entity_type = serializer.validated_data['entity_type']
        entity_id = serializer.validated_data['entity_id']
        category_id = str(serializer.validated_data['category'].id)
        
        try:
            entity_category = self.entity_category_service.link_entity_to_category(
                self.request.user, entity_type, entity_id, category_id
            )
            serializer.instance = entity_category
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        """Delete an entity category using the service layer."""
        try:
            self.entity_category_service.unlink_entity_from_category(
                self.request.user, 
                instance.entity_type, 
                instance.entity_id, 
                str(instance.category.id)
            )
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by_entity')
    def by_entity(self, request):
        """Get categories for a specific entity."""
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')
        
        if not entity_type or not entity_id:
            return Response(
                {'detail': 'entity_type and entity_id parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            entity_categories = self.entity_category_service.get_entity_categories(
                request.user, entity_type, entity_id
            )
            serializer = EntityCategorySerializer(entity_categories, many=True)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
