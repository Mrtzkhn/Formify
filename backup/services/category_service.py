from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from forms.models import Category, EntityCategory, Form, Process
from forms.repositories.category_repository import CategoryRepository, EntityCategoryRepository
from typing import Dict, List, Any


class CategoryService:
    """Service layer for category operations with business logic."""
    
    def __init__(self):
        self.category_repository = CategoryRepository()
        self.entity_category_repository = EntityCategoryRepository()
    
    def create_category(self, user, category_data: Dict[str, Any]) -> Category:
        """
        Create a new category.
        
        Args:
            user: The authenticated user
            category_data: Dictionary containing category data
            
        Returns:
            Category: The created category instance
            
        Raises:
            ValidationError: If category data is invalid
        """
        # Validate category name uniqueness for the user
        existing_category = self.category_repository.get_by_name(
            category_data['name'], 
            str(user.id)
        )
        if existing_category:
            raise ValidationError("A category with this name already exists.")
        
        # Create the category
        category = self.category_repository.create(
            created_by=user,
            **category_data
        )
        
        return category
    
    def get_user_categories(self, user) -> List[Category]:
        """
        Get all categories for user.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[Category]: List of categories belonging to user
        """
        return self.category_repository.get_by_user(str(user.id))
    
    def get_category(self, user, category_id: str) -> Category:
        """
        Get a specific category by ID.
        
        Args:
            user: The authenticated user
            category_id: The category ID
            
        Returns:
            Category: The category instance
            
        Raises:
            ValidationError: If category doesn't exist or doesn't belong to user
        """
        category = self.category_repository.get_by_id(category_id)
        if not category or category.created_by != user:
            raise ValidationError("Category not found.")
        return category
    
    def update_category(self, user, category_id: str, category_data: Dict[str, Any]) -> Category:
        """
        Update an existing category.
        
        Args:
            user: The authenticated user
            category_id: The category ID
            category_data: Dictionary containing updated category data
            
        Returns:
            Category: The updated category instance
            
        Raises:
            ValidationError: If category doesn't exist or doesn't belong to user
        """
        category = self.get_category(user, category_id)
        
        # Check name uniqueness if name is being updated
        if 'name' in category_data and category_data['name'] != category.name:
            existing_category = self.category_repository.get_by_name(
                category_data['name'], 
                str(user.id)
            )
            if existing_category and existing_category.id != category.id:
                raise ValidationError("A category with this name already exists.")
        
        # Update the category
        updated_category = self.category_repository.update(category, **category_data)
        return updated_category
    
    def delete_category(self, user, category_id: str) -> bool:
        """
        Delete a category.
        
        Args:
            user: The authenticated user
            category_id: The category ID
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ValidationError: If category doesn't exist or doesn't belong to user
        """
        category = self.get_category(user, category_id)
        
        # Check if category has any entity associations
        entity_categories = self.entity_category_repository.get_by_category(str(category.id))
        if entity_categories:
            raise ValidationError("Cannot delete category that has entity associations.")
        
        # Delete the category
        return self.category_repository.delete(category)


class EntityCategoryService:
    """Service layer for entity category operations with business logic."""
    
    def __init__(self):
        self.entity_category_repository = EntityCategoryRepository()
        self.category_repository = CategoryRepository()
    
    def link_entity_to_category(self, user, entity_type: str, entity_id: str, category_id: str) -> EntityCategory:
        """
        Link an entity to a category.
        
        Args:
            user: The authenticated user
            entity_type: Type of entity ('form' or 'process')
            entity_id: The entity ID
            category_id: The category ID
            
        Returns:
            EntityCategory: The created entity category instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate category belongs to user
        category = self.category_repository.get_by_id(category_id)
        if not category or category.created_by != user:
            raise ValidationError("Category not found.")
        
        # Validate entity exists and belongs to user
        if entity_type == 'form':
            entity = get_object_or_404(Form, id=entity_id, created_by=user)
        elif entity_type == 'process':
            entity = get_object_or_404(Process, id=entity_id, created_by=user)
        else:
            raise ValidationError("Invalid entity type.")
        
        # Create the entity category link
        entity_category = self.entity_category_repository.link_entity_to_category(
            entity_type, entity_id, category_id
        )
        
        return entity_category
    
    def unlink_entity_from_category(self, user, entity_type: str, entity_id: str, category_id: str) -> bool:
        """
        Unlink an entity from a category.
        
        Args:
            user: The authenticated user
            entity_type: Type of entity ('form' or 'process')
            entity_id: The entity ID
            category_id: The category ID
            
        Returns:
            bool: True if unlinked successfully
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate category belongs to user
        category = self.category_repository.get_by_id(category_id)
        if not category or category.created_by != user:
            raise ValidationError("Category not found.")
        
        # Unlink the entity from category
        return self.entity_category_repository.unlink_entity_from_category(
            entity_type, entity_id, category_id
        )
    
    def get_entity_categories(self, user, entity_type: str, entity_id: str) -> List[EntityCategory]:
        """
        Get all categories for a specific entity.
        
        Args:
            user: The authenticated user
            entity_type: Type of entity ('form' or 'process')
            entity_id: The entity ID
            
        Returns:
            List[EntityCategory]: List of entity category instances
        """
        # Validate entity exists and belongs to user
        if entity_type == 'form':
            entity = get_object_or_404(Form, id=entity_id, created_by=user)
        elif entity_type == 'process':
            entity = get_object_or_404(Process, id=entity_id, created_by=user)
        else:
            raise ValidationError("Invalid entity type.")
        
        return self.entity_category_repository.get_by_entity(entity_type, entity_id)
    
    def get_user_entity_categories(self, user) -> List[EntityCategory]:
        """
        Get all entity categories for user's categories.
        
        Args:
            user: The authenticated user
            
        Returns:
            List[EntityCategory]: List of entity category instances
        """
        return self.entity_category_repository.get_by_user(str(user.id))
