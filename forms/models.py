from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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
    # ERD: add nullable user reference, ip address optional string
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'form view'
        verbose_name_plural = 'form views'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of {self.form.title} at {self.viewed_at}"



class Category(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['name']
        unique_together = ['name', 'created_by']
    
    def __str__(self):
        return self.name



class EntityCategory(models.Model):
    ENTITY_TYPES = [
        ('form', 'Form'),
        ('process', 'Process'),
    ]
    entity_type = models.CharField(max_length=10, choices=ENTITY_TYPES)
    entity_id = models.UUIDField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'entity category'
        verbose_name_plural = 'entity categories'
        ordering = ['-created_at']
        unique_together = ['entity_type', 'entity_id', 'category']
    
    def __str__(self):
        return f"{self.category.name} - {self.get_entity_type_display()}"


class Field(models.Model):
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('select', 'Dropdown Selection'),
        ('checkbox', 'Checkboxes'),
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
        # Validate field options based on field type
        if self.field_type in ['select', 'checkbox']:
            if not self.options.get('choices'):
                raise ValidationError(f"Field type '{self.field_type}' requires choices in options.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Process(models.Model):
    PROCESS_TYPES = [
        ('linear', 'Linear Process'),
        ('free', 'Free Process'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name='process title')
    description = models.TextField(blank=True, verbose_name='description')
    process_type = models.CharField(max_length=10, choices=PROCESS_TYPES, verbose_name='process type')
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
        verbose_name = 'process'
        verbose_name_plural = 'processes'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def step_count(self):
        return self.process_steps.count()
    
    def clean(self):
        # Validate access password for private processes
        if not self.is_public and not self.access_password:
            raise ValidationError("Private processes require an access password.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class ProcessStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='process_steps')
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name='form')
    step_name = models.CharField(max_length=255, verbose_name='step name')
    step_description = models.TextField(blank=True, verbose_name='step description')
    order_num = models.PositiveIntegerField(default=0, verbose_name='order number')
    is_mandatory = models.BooleanField(default=True, verbose_name='mandatory')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'process step'
        verbose_name_plural = 'process steps'
        ordering = ['order_num', 'created_at']
        unique_together = ['process', 'order_num']
    
    def __str__(self):
        return f"{self.step_name} ({self.process.title})"
    
    def clean(self):
        # Validate that the form belongs to the same user as the process
        if self.form.created_by != self.process.created_by:
            raise ValidationError("Process step form must belong to the same user as the process.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Response(models.Model):
    """Model for storing form submissions/responses."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='responses')
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='submitted by'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'response'
        verbose_name_plural = 'responses'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Response to {self.form.title} at {self.submitted_at}"


class Answer(models.Model):
    """Model for storing individual field answers within a response."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, verbose_name='field')
    value = models.TextField(verbose_name='answer value')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'answer'
        verbose_name_plural = 'answers'
        ordering = ['field__order_num', 'created_at']
        unique_together = ['response', 'field']
    
    def __str__(self):
        return f"Answer for {self.field.label}: {self.value[:50]}..."


class Report(models.Model):
    """Reporting configuration per ERD."""
    REPORT_TYPES = [
        ('summary', 'Summary'),
        ('detailed', 'Detailed'),
    ]
    
    SCHEDULE_TYPES = [
        ('manual', 'Manual'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    DELIVERY_METHODS = [
        ('email', 'Email'),
    ]

    id = models.AutoField(primary_key=True)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='reports')
    type = models.CharField(max_length=20, choices=REPORT_TYPES)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default='manual')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='email')
    next_run = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'report'
        verbose_name_plural = 'reports'
        ordering = ['-created_at']

        constraints = [
            models.UniqueConstraint(
                fields=['form', 'type', 'created_by'],
                name='uniq_report_per_user_form_type'
            )
        ]

    def __str__(self):
        return f"Report({self.type}) for {self.form.title}"