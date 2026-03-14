from django.shortcuts import render
from .models import RoommatePost
from rest_framework import viewsets
from .serializers import RoommatePostSerializer
#-------------------------------HTML views--------------------------------#
# Home page
def index(request):
    return render(request, "bear_estate_homepage.html")

# Roommate posting view
def roommate_view(request):
    return render(request, "roommate_postings_view.html")

#-------------------------------API views--------------------------------#
# Roommate Post API
class RoommatePostViewSet(viewsets.ModelViewSet):
    '''
    Recieves all the roommate post objects. Calls the serializer.
    Displays the data in json format.
    '''
    queryset = RoommatePost.objects.all()
    serializer_class = RoommatePostSerializer