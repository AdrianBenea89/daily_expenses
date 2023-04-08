import csv

from datetime import datetime, timedelta
from django.db.models import Q
from django.db.models import Sum, Count

from django.http import HttpResponse
from rest_framework import filters
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings

from daily_expenses_app import models
from daily_expenses_app import permissions
from daily_expenses_app import serializers
from daily_expenses_app.serializers import StatisticsSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    """Handle creating and updating user profiles"""
    serializer_class = serializers.UserProfileSerializer
    queryset = models.UserProfile.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.UpdateOwnProfile,)

    def get_queryset(self):
        """Retrieve only logged in user profile"""
        return self.queryset.filter(email=self.request.user)


class UserLoginApiView(ObtainAuthToken):
    """Handle creating user authentication tokens"""
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        Token.objects.filter(user=user).delete()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
        })


class UserDailyExpensesViewSet(viewsets.ModelViewSet):
    """Handles creating, reading and updating daily expenses"""
    authentication_classes = (TokenAuthentication,)
    serializer_class = serializers.UserDailyExpensesSerializer
    queryset = models.UserDailyExpenses.objects.all()
    permission_classes = [IsAuthenticated,]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('expense_name', 'created_at', 'price')

    def get_queryset(self):
        """Return only logged-in user's expenses"""
        return self.queryset.filter(user=self.request.user).order_by('id')

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.UserDailyExpensesSerializer
        elif self.action == 'upload_image':
            return serializers.ExpensesImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Sets the user profile to the logged in user"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe"""
        expense = self.get_object()
        serializer = self.get_serializer(expense, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    serializer_class = serializers.CategorySerializer
    queryset = models.Category.objects.all()
    permission_classes = (IsAuthenticated, permissions.IsOwner)

    def get_queryset(self):
        return self.queryset.filter(
            Q(user=self.request.user) | Q(user__isnull=True))

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            name = serializer.data['category_name']
            description = serializer.data['description']
            category_name_filter = Q(category_name=name)
            if self.get_queryset().filter(category_name_filter):
                return Response(
                    {'detail': 'You already have this category'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            models.Category.objects.create(
                category_name=name,
                user=request.user,
                description=description
            )
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        """Sets the user profile to the logged in user"""
        serializer.save(user=self.request.user)


class StatisticsViewSet(viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]
    serializer_class = StatisticsSerializer

    def get_queryset(self):
        return models.UserDailyExpenses.objects.filter(
            Q(user=self.request.user))

    def list(self, request):
        queryset = self.get_queryset()
        expenses_by_category = queryset.values(
            'category__category_name').order_by(
            'category').annotate(Sum('price'))
        most_used_categories = self.get_queryset().values_list(
            'category__category_name').annotate(
            name_count=Count('category__category_name')).order_by(
            '-name_count')
        last_1_day = queryset.filter(
            created_at__gte=datetime.now() -
            timedelta(days=1)).aggregate(Sum('price'))
        last_7_days = queryset.filter(
            created_at__gte=datetime.now() -
            timedelta(days=7)).aggregate(Sum('price'))
        last_30_days = queryset.filter(
            created_at__gte=datetime.now() -
            timedelta(days=30)).aggregate(Sum('price'))
        data = {
            'last_1_day': last_1_day,
            'last_7_days': last_7_days,
            'last_30_days': last_30_days,
            'most_used_categories': most_used_categories,
            'expenses_by_category': expenses_by_category
        }
        return Response({'data': data, 'status': status.HTTP_200_OK})


class ExportCSV(viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return models.UserDailyExpenses.objects.filter(user=self.request.user)

    def list(self, request):
        results = self.get_queryset()
        response = HttpResponse('  ')
        response['Content-Disposition'] = 'attachment; filename=expenses.csv'
        writer = csv.writer(response, delimiter=",")
        writer.writerow(["User", "Name", "Price", "Category"])
        expenses_fields = results.values_list(
            'user__email', 'expense_name',
            'price', 'category__category_name')
        for expense in expenses_fields:
            writer.writerow(expense)
        return response
