from typing import List
from forms.models import Category, EntityCategory
from .base_repository import BaseRepository


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


class EntityCategoryRepository(BaseRepository):
    """Repository for EntityCategory model operations."""
    
    def __init__(self):
        super().__init__(EntityCategory)
    
    def get_by_entity(self, entity_type: str, entity_id: str) -> List[EntityCategory]:
        """Get all categories for a specific entity."""
        return list(EntityCategory.objects.filter(
            entity_type=entity_type, 
            entity_id=entity_id
        ).order_by('category__name'))
    
    def get_by_category(self, category_id: str) -> List[EntityCategory]:
        """Get all entities for a specific category."""
        return list(EntityCategory.objects.filter(
            category_id=category_id
        ).order_by('-created_at'))
    
    def get_by_user(self, user_id: str) -> List[EntityCategory]:
        """Get all entity categories for user's categories."""
        return list(EntityCategory.objects.filter(
            category__created_by_id=user_id
        ).order_by('-created_at'))
    
    def link_entity_to_category(self, entity_type: str, entity_id: str, category_id: str) -> EntityCategory:
        """Link an entity to a category."""
        entity_category, created = EntityCategory.objects.get_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            category_id=category_id
        )
        return entity_category
    
    def unlink_entity_from_category(self, entity_type: str, entity_id: str, category_id: str) -> bool:
        """Unlink an entity from a category."""
        try:
            entity_category = EntityCategory.objects.get(
                entity_type=entity_type,
                entity_id=entity_id,
                category_id=category_id
            )
            entity_category.delete()
            return True
        except EntityCategory.DoesNotExist:
            return False
