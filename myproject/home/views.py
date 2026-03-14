from django.shortcuts import render

def index(request):
    return render(request, "bear_estate_homepage.html")

def roommate_view(request):
    return render(request, "roommate_postings_view.html")