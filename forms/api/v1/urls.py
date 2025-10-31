from django.urls import path, include
from rest_framework.routers import DefaultRouter
from forms.api.v1.views import (
    FieldViewSet, FormViewSet, PublicFormViewSet, PrivateFormViewSet,
    ProcessViewSet, ProcessStepViewSet, ProcessWorkflowViewSet,
    CategoryViewSet, EntityCategoryViewSet, ResponseViewSet, AnswerViewSet, ReportViewSet
    )

app_name = 'forms_api_v1'

# Create router for API v1
router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'fields', FieldViewSet, basename='field')
router.register(r'processes', ProcessViewSet, basename='process')
router.register(r'process-steps', ProcessStepViewSet, basename='process-step')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'entity-categories', EntityCategoryViewSet, basename='entity-category')
router.register(r'responses', ResponseViewSet, basename='response')
router.register(r'answers', AnswerViewSet, basename='answer')
router.register(r'', FormViewSet, basename='form')

urlpatterns = [
    path('', include(router.urls)),
    
    # Public form access endpoints
    path('public/forms/', PublicFormViewSet.as_view({'get': 'list'}), name='public-forms-list'),
    path('public/forms/<uuid:pk>/', PublicFormViewSet.as_view({'get': 'retrieve'}), name='public-forms-detail'),
    path('public/forms/<uuid:pk>/submit/', PublicFormViewSet.as_view({'post': 'submit_response'}), name='public-forms-submit'),
    
    # Private form access endpoints
    path('private/forms/validate/', PrivateFormViewSet.as_view({'post': 'validate_access'}), name='private-forms-validate'),
    
    # Process workflow endpoints
    path('workflow/process-steps/', ProcessWorkflowViewSet.as_view({'get': 'get_process_steps'}), name='workflow-process-steps'),
    path('workflow/current-step/', ProcessWorkflowViewSet.as_view({'get': 'get_current_step'}), name='workflow-current-step'),
    path('workflow/complete-step/', ProcessWorkflowViewSet.as_view({'post': 'complete_step'}), name='workflow-complete-step'),
    path('workflow/progress/', ProcessWorkflowViewSet.as_view({'get': 'get_process_progress'}), name='workflow-progress'),
]
