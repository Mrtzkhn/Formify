from abc import ABC
from typing import List, Optional, Any, Dict
from django.db import models


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
    
    def filter(self, **kwargs) -> List[models.Model]:
        """Filter objects by given criteria."""
        return list(self.model.objects.filter(**kwargs))
    
    def exists(self, **kwargs) -> bool:
        """Check if object exists with given criteria."""
        return self.model.objects.filter(**kwargs).exists()
    
    def count(self, **kwargs) -> int:
        """Count objects with given criteria."""
        return self.model.objects.filter(**kwargs).count()
