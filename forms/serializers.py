
from rest_framework import serializers
from django.core.exceptions import ValidationError
from forms.models import Form, Field, Process, ProcessStep, Category, EntityCategory, Response, Answer


# Form Serializers
class FormSerializer(serializers.ModelSerializer):
    """Serializer for displaying form data."""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    field_count = serializers.SerializerMethodField()
    view_count = serializers.ReadOnlyField()
    response_count = serializers.ReadOnlyField()

    class Meta:
        model = Form
        fields = [
            'id', 'title', 'description', 'created_by', 'created_by_name',
            'is_public', 'access_password', 'is_active', 'field_count',
            'view_count', 'response_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_field_count(self, obj):
        """Get the number of fields in this form."""
        return obj.fields.count()


class FormCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new forms."""
    
    class Meta:
        model = Form
        fields = ['title', 'description', 'is_public', 'access_password', 'is_active']
    
    def validate_access_password(self, value):
        """Validate access password for private forms."""
        is_public = self.initial_data.get('is_public', True)
        if not is_public and not value:
            raise serializers.ValidationError("Private forms require an access password.")
        return value


class FormUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing forms."""
    
    class Meta:
        model = Form
        fields = ['title', 'description', 'is_public', 'access_password', 'is_active']

    def validate_access_password(self, value):
        """Validate access password for private forms."""
        is_public = self.initial_data.get('is_public', True)
        if not is_public and not value:
            raise serializers.ValidationError("Private forms require an access password.")
        return value


class FormListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for form lists."""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    field_count = serializers.SerializerMethodField()
    view_count = serializers.ReadOnlyField()
    response_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Form
        fields = [
            'id', 'title', 'description', 'created_by_name', 'is_public',
            'is_active', 'field_count', 'view_count', 'response_count', 'created_at'
        ]
    
    def get_field_count(self, obj):
        """Get the number of fields in this form."""
        return obj.fields.count()


class PublicFormSerializer(serializers.ModelSerializer):
    """Serializer for public form access (without sensitive data)."""
    field_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Form
        fields = [
            'id', 'title', 'description', 'is_public', 'field_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_field_count(self, obj):
        """Get the number of fields in this form."""
        return obj.fields.count()


class PublicFormAccessSerializer(serializers.Serializer):
    """Serializer for validating private form access."""
    form_id = serializers.UUIDField()
    password = serializers.CharField(max_length=255)


class FieldSerializer(serializers.ModelSerializer):
    """Serializer for displaying field data."""
    field_type_display = serializers.CharField(source='get_field_type_display', read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)
    
    class Meta:
        model = Field
        fields = [
            'id', 'form', 'form_title', 'label', 'field_type', 'field_type_display',
            'is_required', 'options', 'order_num', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FieldCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new fields."""
    
    class Meta:
        model = Field
        fields = ['form', 'label', 'field_type', 'is_required', 'options', 'order_num']
    
    def validate_options(self, value):
        """Validate field options based on field type."""
        field_type = self.initial_data.get('field_type')
        if not field_type:
            return value
        
        # Import here to avoid circular imports
        from forms.services.services import FieldService
        
        try:
            field_service = FieldService()
            field_service.validate_field_options(field_type, value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def validate_form(self, value):
        """Ensure user owns the form."""
        user = self.context['request'].user
        if value.created_by != user:
            raise serializers.ValidationError("You can only add fields to your own forms.")
        return value


class FieldUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing fields."""
    
    class Meta:
        model = Field
        fields = ['label', 'field_type', 'is_required', 'options', 'order_num']
    
    def validate_options(self, value):
        """Validate field options based on field type."""
        field_type = self.initial_data.get('field_type', self.instance.field_type if self.instance else None)
        if not field_type:
            return value
        
        # Import here to avoid circular imports
        from forms.services.services import FieldService
        
        try:
            field_service = FieldService()
            field_service.validate_field_options(field_type, value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value


class FieldListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for field lists."""
    field_type_display = serializers.CharField(source='get_field_type_display', read_only=True)
    
    class Meta:
        model = Field
        fields = ['id', 'label', 'field_type', 'field_type_display', 'is_required', 'order_num']


class FieldReorderSerializer(serializers.Serializer):
    """Serializer for field reordering."""
    new_order = serializers.IntegerField(min_value=1)
    
    def validate_new_order(self, value):
        """Validate the new order number."""
        field = self.context['field']
        max_order = Field.objects.filter(form=field.form).count()
        
        if value > max_order:
            raise serializers.ValidationError(f"Order number cannot exceed {max_order}.")
        
        return value


class ProcessSerializer(serializers.ModelSerializer):
    """Serializer for displaying process data."""
    step_count = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    process_steps = serializers.SerializerMethodField()

    class Meta:
        model = Process
        fields = [
            'id', 'title', 'description', 'process_type', 'created_by', 'created_by_name',
            'is_public', 'access_password', 'is_active', 'step_count', 'process_steps',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_process_steps(self, obj):
        """Get process steps ordered by order_num."""
        steps = obj.process_steps.all().order_by('order_num')
        return ProcessStepListSerializer(steps, many=True).data


class ProcessCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating processes."""
    
    class Meta:
        model = Process
        fields = [
            'title', 'description', 'process_type', 'is_public', 'access_password'
        ]
    
    def validate(self, data):
        """Validate the entire data set."""
        is_public = data.get('is_public', True)
        access_password = data.get('access_password')
        
        # Handle both boolean and string values
        if isinstance(is_public, bool):
            is_public_value = is_public
        else:
            is_public_value = str(is_public).lower() not in ['false', '0']
        
        if not is_public_value and not access_password:
            raise serializers.ValidationError({
                'access_password': "Private processes require an access password."
            })
        
        return data
    
    def validate_process_type(self, value):
        """Validate process type."""
        valid_types = [choice[0] for choice in Process.PROCESS_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Process type must be one of: {', '.join(valid_types)}")
        return value


class ProcessUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating processes."""
    
    class Meta:
        model = Process
        fields = [
            'title', 'description', 'process_type', 'is_public', 'access_password'
        ]
    
    def validate(self, data):
        """Validate the entire data set."""
        is_public = data.get('is_public')
        access_password = data.get('access_password')
        
        # If is_public is not being updated, use the current value
        if 'is_public' not in data:
            is_public = self.instance.is_public if self.instance else True
        
        # Handle both boolean and string values
        if isinstance(is_public, bool):
            is_public_value = is_public
        else:
            is_public_value = str(is_public).lower() not in ['false', '0']
        
        # If access_password is not being updated, use the current value
        if 'access_password' not in data:
            access_password = self.instance.access_password if self.instance else None
        
        if not is_public_value and not access_password:
            raise serializers.ValidationError({
                'access_password': "Private processes require an access password."
            })
        
        return data


class ProcessListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for process lists."""
    step_count = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Process
        fields = [
            'id', 'title', 'description', 'process_type', 'created_by_name',
            'is_public', 'is_active', 'step_count', 'created_at'
        ]


class ProcessStepSerializer(serializers.ModelSerializer):
    """Serializer for displaying process step data."""
    form_title = serializers.CharField(source='form.title', read_only=True)
    form_description = serializers.CharField(source='form.description', read_only=True)
    
    class Meta:
        model = ProcessStep
        fields = [
            'id', 'process', 'form', 'form_title', 'form_description',
            'step_name', 'step_description', 'order_num', 'is_mandatory',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProcessStepCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating process steps."""
    
    class Meta:
        model = ProcessStep
        fields = [
            'process', 'form', 'step_name', 'step_description', 'order_num', 'is_mandatory'
        ]
    
    def validate_form(self, value):
        """Validate that the form belongs to the authenticated user."""
        if value.created_by != self.context['request'].user:
            raise serializers.ValidationError("You can only use forms you created.")
        return value
    
    def validate_process(self, value):
        """Validate that the process belongs to the authenticated user."""
        if value.created_by != self.context['request'].user:
            raise serializers.ValidationError("You can only add steps to processes you created.")
        return value

    def validate_order_num(self, value):
        """Validate order number."""
        if value < 1:
            raise serializers.ValidationError("Order number must be at least 1.")
        return value


class ProcessStepUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating process steps."""
    
    class Meta:
        model = ProcessStep
        fields = [
            'step_name', 'step_description', 'order_num', 'is_mandatory'
        ]
    
    def validate_order_num(self, value):
        """Validate order number."""
        if value < 1:
            raise serializers.ValidationError("Order number must be at least 1.")
        return value


class ProcessStepListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for process step lists."""
    form_title = serializers.CharField(source='form.title', read_only=True)
    
    class Meta:
        model = ProcessStep
        fields = [
            'id', 'form', 'form_title', 'step_name', 'order_num', 'is_mandatory'
        ]


class ProcessStepReorderSerializer(serializers.Serializer):
    """Serializer for reordering process steps."""
    new_order = serializers.IntegerField(min_value=1)


# Category Serializers
class CategorySerializer(serializers.ModelSerializer):
    """Serializer for displaying category data."""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating categories."""
    class Meta:
        model = Category
        fields = ['name', 'description']


class CategoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating categories."""
    class Meta:
        model = Category
        fields = ['name', 'description']


class CategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for category lists."""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_by_name', 'created_at']


# EntityCategory Serializers
class EntityCategorySerializer(serializers.ModelSerializer):
    """Serializer for displaying entity category data."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    
    class Meta:
        model = EntityCategory
        fields = [
            'id', 'entity_type', 'entity_type_display', 'entity_id', 
            'category', 'category_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EntityCategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating entity categories."""
    class Meta:
        model = EntityCategory
        fields = ['entity_type', 'entity_id', 'category']
    
    def validate_category(self, value):
        """Validate that the category belongs to the authenticated user."""
        if value.created_by != self.context['request'].user:
            raise serializers.ValidationError("You can only use categories you created.")
        return value


# Response Serializers
class ResponseSerializer(serializers.ModelSerializer):
    """Serializer for displaying response data."""
    submitted_by_name = serializers.CharField(source='submitted_by.full_name', read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)
    answer_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Response
        fields = [
            'id', 'form', 'form_title', 'submitted_by', 'submitted_by_name',
            'ip_address', 'user_agent', 'submitted_at', 'answer_count'
        ]
        read_only_fields = ['id', 'submitted_by', 'ip_address', 'user_agent', 'submitted_at']
    
    def get_answer_count(self, obj):
        """Get the number of answers in this response."""
        return obj.answers.count()


class ResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating responses."""
    answers = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="List of answers with field_id and value"
    )
    
    class Meta:
        model = Response
        fields = ['form', 'answers']
    
    def validate_form(self, value):
        """Validate that the form is active and accessible."""
        if not value.is_active:
            raise serializers.ValidationError("Cannot submit to inactive form.")
        return value
    
    def validate_answers(self, value):
        """Validate answers data."""
        if not value:
            raise serializers.ValidationError("At least one answer is required.")
        
        # Validate that all answers have required fields
        for answer in value:
            if 'field_id' not in answer or 'value' not in answer:
                raise serializers.ValidationError("Each answer must have 'field_id' and 'value'.")
        
        return value


class ResponseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for response lists."""
    submitted_by_name = serializers.CharField(source='submitted_by.full_name', read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)
    
    class Meta:
        model = Response
        fields = [
            'id', 'form_title', 'submitted_by_name', 'submitted_at'
        ]


# Answer Serializers
class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for displaying answer data."""
    field_label = serializers.CharField(source='field.label', read_only=True)
    field_type = serializers.CharField(source='field.field_type', read_only=True)
    response_id = serializers.CharField(source='response.id', read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id', 'response', 'response_id', 'field', 'field_label', 
            'field_type', 'value', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnswerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating answers."""
    class Meta:
        model = Answer
        fields = ['response', 'field', 'value']
    
    def validate_field(self, value):
        """Validate that the field belongs to the response's form."""
        response = self.initial_data.get('response')
        if response and value.form != response.form:
            raise serializers.ValidationError("Field must belong to the same form as the response.")
        return value


class AnswerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for answer lists."""
    field_label = serializers.CharField(source='field.label', read_only=True)
    field_type = serializers.CharField(source='field.field_type', read_only=True)
    
    class Meta:
        model = Answer
        fields = ['id', 'field_label', 'field_type', 'value', 'created_at']