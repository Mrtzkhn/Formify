from random import choice, choices
from tabnanny import verbose
from tkinter import CASCADE
import django
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