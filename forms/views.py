
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Form, FormView, Category
from .serializers import FormSerializer, FormCreateSerializer, FormViewSerializer, CategorySerializer

class FormViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FormCreateSerializer
        return FormSerializer

    def get_queryset(self):
        return Form.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def public(self, request, pk=None):
        form = get_object_or_404(Form, id=pk, is_public=True, is_active=True)

        FormView.objects.create(
            form=form,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        serializer = FormSerializer(form)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        form = get_object_or_404(Form, id=pk, created_by=request.user)
        stats = {
            'form_id': str(form.id),
            'title': form.title,
            'view_count': form.view_count,
            'response_count': form.response_count,
            'created_at': form.created_at,
            'last_viewed': form.formview_set.last().viewed_at if form.formview_set.exists() else None
        }
        return Response(stats, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(created_by=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)