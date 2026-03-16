from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

# Routers for API view
router = DefaultRouter()
router.register('', views.RoommatePostViewSet, basename='rm_post')

urlpatterns = [
    path('view/', views.roommate_view, name='rm_view'),
    path('api/', include(router.urls)),

]