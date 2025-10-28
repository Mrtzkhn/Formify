from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Form, Field, Process, ProcessStep, Category, EntityCategory, 
    Response, Answer, FormView
)


class FieldInline(admin.TabularInline):
    model = Field
    extra = 1
    fields = ('label', 'field_type', 'is_required', 'order_num')
    ordering = ('order_num',)


class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    extra = 1
    fields = ('step_name', 'form', 'order_num', 'is_mandatory')
    ordering = ('order_num',)


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_public', 'is_active', 'field_count', 'response_count', 'view_count', 'created_at')
    list_filter = ('is_public', 'is_active', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'created_by__email', 'created_by__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'view_count', 'response_count', 'api_url')
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'description', 'created_by')
        }),
        ('Access Control', {
            'fields': ('is_public', 'access_password', 'is_active')
        }),
        ('Statistics', {
            'fields': ('view_count', 'response_count'),
            'classes': ('collapse',)
        }),
        ('API Information', {
            'fields': ('api_url',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [FieldInline]
    
    def field_count(self, obj):
        return obj.fields.count()
    field_count.short_description = 'Fields'
    
    def response_count(self, obj):
        return obj.responses.count()
    response_count.short_description = 'Responses'
    
    def api_url(self, obj):
        if obj.id:
            url = reverse('admin:forms_form_change', args=[obj.id])
            return format_html('<a href="{}" target="_blank">View in Admin</a>', url)
        return '-'
    api_url.short_description = 'Admin Link'


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('label', 'form', 'field_type', 'is_required', 'order_num', 'created_at')
    list_filter = ('field_type', 'is_required', 'created_at', 'form__created_by')
    search_fields = ('label', 'form__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'options_preview')
    fieldsets = (
        (None, {
            'fields': ('id', 'form', 'label', 'field_type', 'is_required', 'order_num')
        }),
        ('Options', {
            'fields': ('options', 'options_preview'),
            'description': 'For select and checkbox fields, provide choices in JSON format: {"choices": ["Option 1", "Option 2"]}'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def options_preview(self, obj):
        if obj.options:
            choices = obj.options.get('choices', [])
            if choices:
                return format_html('<strong>Choices:</strong><br>{}', '<br>'.join(f'• {choice}' for choice in choices))
        return 'No options configured'
    options_preview.short_description = 'Options Preview'


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'process_type', 'is_public', 'is_active', 'step_count', 'created_at')
    list_filter = ('process_type', 'is_public', 'is_active', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'created_by__email', 'created_by__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'step_count', 'api_url')
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'description', 'process_type', 'created_by')
        }),
        ('Access Control', {
            'fields': ('is_public', 'access_password', 'is_active')
        }),
        ('Statistics', {
            'fields': ('step_count',),
            'classes': ('collapse',)
        }),
        ('API Information', {
            'fields': ('api_url',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ProcessStepInline]
    
    def step_count(self, obj):
        return obj.process_steps.count()
    step_count.short_description = 'Steps'
    
    def api_url(self, obj):
        if obj.id:
            url = reverse('admin:forms_process_change', args=[obj.id])
            return format_html('<a href="{}" target="_blank">View in Admin</a>', url)
        return '-'
    api_url.short_description = 'Admin Link'


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ('step_name', 'process', 'form', 'order_num', 'is_mandatory', 'created_at')
    list_filter = ('is_mandatory', 'created_at', 'process__created_by')
    search_fields = ('step_name', 'process__title', 'form__title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'process', 'form', 'step_name', 'step_description', 'order_num')
        }),
        ('Step Settings', {
            'fields': ('is_mandatory',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'entity_count', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('name', 'description', 'created_by__email', 'created_by__full_name')
    readonly_fields = ('created_at', 'entity_count')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Statistics', {
            'fields': ('entity_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def entity_count(self, obj):
        return obj.entitycategory_set.count()
    entity_count.short_description = 'Entities'


@admin.register(EntityCategory)
class EntityCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'entity_type', 'entity_title', 'created_at')
    list_filter = ('entity_type', 'created_at', 'category__created_by')
    search_fields = ('category__name', 'entity_id')
    readonly_fields = ('created_at', 'entity_title')
    fieldsets = (
        (None, {
            'fields': ('entity_type', 'entity_id', 'category', 'entity_title')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def entity_title(self, obj):
        if obj.entity_type == 'form':
            try:
                form = Form.objects.get(id=obj.entity_id)
                return form.title
            except Form.DoesNotExist:
                return 'Form not found'
        elif obj.entity_type == 'process':
            try:
                process = Process.objects.get(id=obj.entity_id)
                return process.title
            except Process.DoesNotExist:
                return 'Process not found'
        return '-'
    entity_title.short_description = 'Entity Title'


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('field', 'value', 'created_at')
    fields = ('field', 'value', 'created_at')
    can_delete = False


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('form', 'submitted_by', 'ip_address', 'submitted_at', 'answer_count')
    list_filter = ('submitted_at', 'form__created_by')
    search_fields = ('form__title', 'submitted_by__email', 'submitted_by__full_name', 'ip_address')
    readonly_fields = ('id', 'submitted_at', 'answer_count', 'api_url')
    fieldsets = (
        (None, {
            'fields': ('id', 'form', 'submitted_by')
        }),
        ('Submission Info', {
            'fields': ('ip_address', 'user_agent', 'submitted_at')
        }),
        ('Statistics', {
            'fields': ('answer_count',),
            'classes': ('collapse',)
        }),
        ('API Information', {
            'fields': ('api_url',),
            'classes': ('collapse',)
        }),
    )
    inlines = [AnswerInline]
    
    def answer_count(self, obj):
        return obj.answers.count()
    answer_count.short_description = 'Answers'
    
    def api_url(self, obj):
        if obj.id:
            url = reverse('admin:forms_response_change', args=[obj.id])
            return format_html('<a href="{}" target="_blank">View in Admin</a>', url)
        return '-'
    api_url.short_description = 'Admin Link'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('field', 'response', 'value_preview', 'created_at')
    list_filter = ('created_at', 'field__field_type', 'field__form__created_by')
    search_fields = ('field__label', 'value', 'response__form__title')
    readonly_fields = ('id', 'created_at', 'value_preview')
    fieldsets = (
        (None, {
            'fields': ('id', 'response', 'field', 'value')
        }),
        ('Preview', {
            'fields': ('value_preview',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def value_preview(self, obj):
        if len(obj.value) > 100:
            return format_html('<div style="max-width: 300px; word-wrap: break-word;">{}</div>', obj.value)
        return obj.value
    value_preview.short_description = 'Value Preview'


@admin.register(FormView)
class FormViewAdmin(admin.ModelAdmin):
    list_display = ('form', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at', 'form__created_by')
    search_fields = ('form__title', 'ip_address')
    readonly_fields = ('viewed_at',)
    fieldsets = (
        (None, {
            'fields': ('form', 'ip_address', 'user_agent', 'viewed_at')
        }),
    )
