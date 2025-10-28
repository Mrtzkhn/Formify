from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from forms.models import Process, ProcessStep, Form, Response as FormResponse
from forms.serializers import (
    ProcessSerializer, ProcessStepSerializer, PublicFormSerializer,
    ResponseSerializer
)
from forms.services.process_service import ProcessService, ProcessStepService
from forms.services.form_service import FormService
from forms.services.response_service import ResponseService


@extend_schema_view(
    get_process_steps=extend_schema(
        summary="Get Process Steps",
        description="Get all steps for a specific process",
        tags=["Process Workflow"]
    ),
    get_current_step=extend_schema(
        summary="Get Current Step",
        description="Get the current step for a process based on completion status",
        tags=["Process Workflow"]
    ),
    complete_step=extend_schema(
        summary="Complete Process Step",
        description="Complete a process step by submitting the form",
        tags=["Process Workflow"]
    ),
    get_process_progress=extend_schema(
        summary="Get Process Progress",
        description="Get the completion progress of a process",
        tags=["Process Workflow"]
    )
)
class ProcessWorkflowViewSet(viewsets.ViewSet):
    """
    ViewSet for process-based form completion workflow.
    """
    permission_classes = [permissions.AllowAny]  # Allow anonymous access for respondents
    process_service = ProcessService()
    process_step_service = ProcessStepService()
    form_service = FormService()
    response_service = ResponseService()

    @action(detail=False, methods=['get'])
    def get_process_steps(self, request):
        """Get all steps for a specific process."""
        try:
            process_id = request.query_params.get('process_id')
            if not process_id:
                return Response(
                    {'detail': 'process_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the process
            process = self.process_service.get_process_by_id(process_id)
            if not process:
                return Response(
                    {'detail': 'Process not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if process is public or user has access
            if not process.is_public:
                # For private processes, we might need password validation
                password = request.query_params.get('password')
                if not password or not self.process_service.validate_process_access(process_id, password):
                    return Response(
                        {'detail': 'This process requires a password'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Get process steps
            steps = self.process_step_service.get_process_steps_public(process_id)
            serializer = ProcessStepSerializer(steps, many=True)
            
            return Response({
                'process': ProcessSerializer(process).data,
                'steps': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_current_step(self, request):
        """Get the current step for a process based on completion status."""
        try:
            process_id = request.query_params.get('process_id')
            if not process_id:
                return Response(
                    {'detail': 'process_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the process
            process = self.process_service.get_process_by_id(process_id)
            if not process:
                return Response(
                    {'detail': 'Process not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check access
            if not process.is_public:
                password = request.query_params.get('password')
                if not password or not self.process_service.validate_process_access(process_id, password):
                    return Response(
                        {'detail': 'This process requires a password'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Get process steps ordered by order_num
            steps = self.process_step_service.get_process_steps_public(process_id)
            
            # For linear processes, find the first incomplete step
            if process.process_type == 'linear':
                for step in steps:
                    # Check if this step has been completed
                    if not self._is_step_completed(step):
                        form = self.form_service.get_form_with_fields(str(step.form.id))
                        return Response({
                            'current_step': ProcessStepSerializer(step).data,
                            'form': PublicFormSerializer(form).data,
                            'is_completed': False
                        }, status=status.HTTP_200_OK)
                
                # All steps completed
                return Response({
                    'current_step': None,
                    'form': None,
                    'is_completed': True,
                    'message': 'All steps completed'
                }, status=status.HTTP_200_OK)
            
            # For free processes, return all steps
            else:
                step_data = []
                for step in steps:
                    form = self.form_service.get_form_with_fields(str(step.form.id))
                    step_data.append({
                        'step': ProcessStepSerializer(step).data,
                        'form': PublicFormSerializer(form).data,
                        'is_completed': self._is_step_completed(step)
                    })
                
                return Response({
                    'steps': step_data,
                    'process_type': 'free'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def complete_step(self, request):
        """Complete a process step by submitting the form."""
        try:
            step_id = request.data.get('step_id')
            answers_data = request.data.get('answers', [])
            
            if not step_id:
                return Response(
                    {'detail': 'step_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the process step
            step = self.process_step_service.get_process_step_by_id(step_id)
            if not step:
                return Response(
                    {'detail': 'Process step not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check access to the process
            process = step.process
            if not process.is_public:
                password = request.data.get('password')
                if not password or not self.process_service.validate_process_access(str(process.id), password):
                    return Response(
                        {'detail': 'This process requires a password'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Submit the response
            ip_address = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            response = self.response_service.submit_response(
                form_id=str(step.form.id),
                answers_data=answers_data,
                ip_address=ip_address,
                user_agent=user_agent,
                submitted_by=None  # Anonymous submission
            )
            
            # Get the next step for linear processes
            next_step = None
            if process.process_type == 'linear':
                next_step = self._get_next_step(process, step)
            
            serializer = ResponseSerializer(response)
            return Response({
                'response': serializer.data,
                'next_step': ProcessStepSerializer(next_step).data if next_step else None,
                'is_process_complete': self._is_process_complete(process)
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_process_progress(self, request):
        """Get the completion progress of a process."""
        try:
            process_id = request.query_params.get('process_id')
            if not process_id:
                return Response(
                    {'detail': 'process_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the process
            process = self.process_service.get_process_by_id(process_id)
            if not process:
                return Response(
                    {'detail': 'Process not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check access
            if not process.is_public:
                password = request.query_params.get('password')
                if not password or not self.process_service.validate_process_access(process_id, password):
                    return Response(
                        {'detail': 'This process requires a password'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Get process steps
            steps = self.process_step_service.get_process_steps_public(process_id)
            
            completed_steps = 0
            total_steps = len(steps)
            
            for step in steps:
                if self._is_step_completed(step):
                    completed_steps += 1
            
            progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            return Response({
                'process': ProcessSerializer(process).data,
                'progress': {
                    'completed_steps': completed_steps,
                    'total_steps': total_steps,
                    'percentage': round(progress_percentage, 2),
                    'is_complete': completed_steps == total_steps
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _is_step_completed(self, step):
        """Check if a process step has been completed."""
        # Check if there are any responses for the form in this step
        return FormResponse.objects.filter(form=step.form).exists()

    def _get_next_step(self, process, current_step):
        """Get the next step in a linear process."""
        steps = self.process_step_service.get_process_steps_public(str(process.id))
        for i, step in enumerate(steps):
            if step.id == current_step.id and i + 1 < len(steps):
                return steps[i + 1]
        return None

    def _is_process_complete(self, process):
        """Check if all steps in a process are completed."""
        steps = self.process_step_service.get_process_steps_public(str(process.id))
        return all(self._is_step_completed(step) for step in steps)
