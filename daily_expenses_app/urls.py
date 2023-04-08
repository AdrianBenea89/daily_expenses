from django.urls import (path, include,)
from rest_framework.routers import DefaultRouter
from daily_expenses_app import views
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

router = DefaultRouter()
router.register('profile', views.UserProfileViewSet)
router.register('expenses', views.UserDailyExpensesViewSet)
router.register('categories', views.CategoryViewSet)
router.register('statistics', views.StatisticsViewSet, basename='statistics/')
router.register('csv-export', views.ExportCSV, basename='csv-export/'),

app_name = 'daily_expenses_app'

schema_view = get_schema_view(
    openapi.Info(title='Daily Expenses API', default_version='v1'),
    public=True,
    # permission_classes=(permissions.IsAuthenticated,)
    permission_classes=[permissions.AllowAny,]
)

urlpatterns = [
    path('login/', views.UserLoginApiView.as_view()),
    path('', include(router.urls)),
]
urlpatterns += [
    path(
        'docs/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui',
    )
]
