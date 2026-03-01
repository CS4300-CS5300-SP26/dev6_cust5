from django.shortcuts import render

def index(request):
    return render(request, "bear_estate_homepage.html")
