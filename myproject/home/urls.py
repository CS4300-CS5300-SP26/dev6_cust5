from django.urls import include, path
from . import views

urlpatterns = [
    path('view/', views.roommate_view, name='rm_view')
    #path('post/', views., name='rm_post')


]