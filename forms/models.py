from django.db import models
from django.contrib.auth import get_user_model
import uuid

# Create your models here.
User = get_user_model()

class Form(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name='form title')
    description = models.TextField(blank=True, verbose_name='description')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='creator'
    )

    is_public = models.BooleanField(default=True, verbose_name='public')
    access_password = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='access password'
    )
    is_active = models.BooleanField(default=True, verbose_name='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'form'
        verbose_name_plural = 'forms'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    @property
    def view_count(self):
        return self.formview_set.count()

    @property
    def response_count(self):
        return self.responses.count()





class FormView(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    viewed_at = models.DateTimeField(auto_now_add=True)



class Category(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)



class EntityCategory(models.Model):
    ENTITY_TYPES = [
        ('form', 'Form'),
        ('process', 'Process'),
    ]
    entity_type = models.CharField(max_length=10, choices=ENTITY_TYPES)
    entity_id = models.UUIDField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Field(models.Model):
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Long Text'),
        ('number', 'Number Input'),
        ('email', 'Email Input'),
        ('url', 'URL Input'),
        ('date', 'Date Picker'),
        ('time', 'Time Picker'),
        ('datetime', 'Date and Time'),
        ('select', 'Dropdown Selection'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes'),
        ('multiselect', 'Multiple Selection'),
        ('boolean', 'Yes/No'),
        ('file', 'File Upload'),
        ('rating', 'Rating Scale'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=255, verbose_name='field label')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, verbose_name='field type')
    is_required = models.BooleanField(default=False, verbose_name='required')
    options = models.JSONField(default=dict, blank=True, verbose_name='field options')
    order_num = models.PositiveIntegerField(default=0, verbose_name='order number')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'field'
        verbose_name_plural = 'fields'
        ordering = ['order_num', 'created_at']
        unique_together = ['form', 'order_num']
    
    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate field options based on field type
        if self.field_type in ['select', 'radio', 'checkbox', 'multiselect']:
            if not self.options.get('choices'):
                raise ValidationError(f"Field type '{self.field_type}' requires choices in options.")
        
        if self.field_type == 'rating':
            min_val = self.options.get('min_value', 1)
            max_val = self.options.get('max_value', 5)
            if min_val >= max_val:
                raise ValidationError("Rating min_value must be less than max_value.")
        
        if self.field_type == 'file':
            allowed_types = self.options.get('allowed_types', [])
            if not allowed_types:
                raise ValidationError("File field requires allowed_types in options.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)