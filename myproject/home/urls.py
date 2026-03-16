from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

# Routers for API view
router = DefaultRouter()
router.register('', views.RoommatePostViewSet, basename='rm_post')

urlpatterns = [
    path('view/', views.search, name='rm_view'),
    path('api/', include(router.urls)),
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),

]
