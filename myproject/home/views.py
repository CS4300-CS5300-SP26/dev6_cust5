from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from rest_framework import viewsets

from .models import RoommatePost, Property
from .serializers import RoommatePostSerializer
from .forms import CustomRegisterForm, RoommatePostForm
from .rentcast_api import get_properties

import json
import requests

# ------------------------------- HTML views -------------------------------- #

# ✅ SEARCH PAGE (FIXED)
def search(request):
    properties = Property.objects.all()

    return render(request, "search.html", {
        "properties": properties
    })

# See all roommate posts
def roommate_list(request):
    posts = RoommatePost.objects.all().order_by('-date')
    return render(request, 'roommate_postings_view.html', {'posts': posts})

# Creates a roommate post 
# Requires user to be logged in
@login_required
def roommate_create(request):
    if request.method == 'POST':
        form = RoommatePostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('roommate_list')
    else:
        form = RoommatePostForm(initial={'date': timezone.now().date()})

    return render(request, 'roommate_create.html', {'form': form})

# Changes roommate post status to closed
# Requires user to be logged in (can only close own posts)
@login_required
def roommate_close(request, post_id):
    post = get_object_or_404(RoommatePost, id=post_id, user=request.user)

    if request.method == 'POST':
        post.status = 'closed'
        post.save()

    return redirect('roommate_list')

# Deletes a roommate post
# Login required
@login_required
def roommate_delete(request, post_id):
    post = get_object_or_404(RoommatePost, id=post_id, user=request.user)

    if request.method == 'POST':
        post.delete()

    return redirect('roommate_list')

# Home page
def index(request):
    context = {}

    # ---------------- LOGIN HANDLING ----------------
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('bear_estate_homepage')
        else:
            context['login_error'] = 'Invalid username or password.'
            context['show_login_modal'] = True

    # ---------------- PROPERTY SEARCH ----------------
    properties = Property.objects.none()

    location = request.GET.get("location", "").strip()
    listing_type = request.GET.get("mode", "").strip()
    property_type = request.GET.get("type", "").strip()
    price_range = request.GET.get("budget", "").strip()

    api_properties = []

    min_price, max_price = None, None
    if price_range and price_range != "any":
        try:
            min_price, max_price = map(int, price_range.split("-"))
        except ValueError:
            pass

    if location:
        properties = Property.objects.filter(location__icontains=location)

        try:
            api_properties = get_properties(
                location,
                property_type=property_type,
                min_price=min_price,
                max_price=max_price,
            )
        except Exception as e:
            print("API Error:", e)
            api_properties = []

    if listing_type in ["rent", "buy"]:
        properties = properties.filter(listing_type=listing_type)

    if property_type and property_type.lower() != "any type":
        properties = properties.filter(property_type=property_type.lower())

    if min_price is not None and max_price is not None:
        properties = properties.filter(price__gte=min_price, price__lte=max_price)

    context.update({
        "properties": properties,
        "api_properties": api_properties,
        "selected_location": location,
        "selected_intent": listing_type,
        "selected_type": property_type,
        "selected_budget": price_range,
        "result_count": properties.count(),
    })

    return render(request, "bear_estate_homepage.html", context)


# User Register
def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('bear_estate_homepage')
        else:
            errors = [error for field in form for error in field.errors]
            errors += list(form.non_field_errors())

            return render(request, 'bear_estate_homepage.html', {
                'show_signup_modal': True,
                'register_errors': errors,
            })

    return redirect('bear_estate_homepage')

# Map view
def map_view(request):
    '''
    Handles input from the search bar on the map page. Uses the US Census Bureau geocoder 
    to convert the address into coordinates. Passes the coordinates to the template to 
    display the map centered on the searched location.
    '''
    searched_location = None        # holds input from search bar (defaults to none if there is no input)

    # if there is an input (POST request) from the search bar
    # generates the coordinates with the Census Bureau API (limited to the US)
    if request.method == 'POST':
        address = request.POST.get('address')
        print('ADDRESS RECIEVED')
        # checks if the address could be found (syntax is correct and location exists)
        if address:
            location = geocode_residential(address)
            if location:
                searched_location = {
                    # NOTE: stores the coordinates as context for the template. Can update to work with model later.
                    # Output will be in json format: {'lat': #, 'lng': #}
                    'lat': location[0],
                    'lng': location[1],
                }

    # Fetches all properties with valid coordinates to display on the map
    # For displaying all availbe locations in an area. Could incorporate Rentcast API properties here as well.
    all_properties = Property.objects.exclude(latitude=None, longitude=None)

    # context for the HTML
    # properties represents markers on the map
    # searched_location centers the map on the searched address and places a marker (resets on page load)
    context = {
        'properties': json.dumps(list(all_properties.values('latitude', 'longitude', 'location'))),
        'searched_location': json.dumps(searched_location) if searched_location else 'null'
    }
    return render(request, 'map.html', context)

# Geocode helper function
def geocode_residential(address):
    '''
    Uses the US Census Bureau API to convert an address to coordinates.
    Returns a tuple of (latitude, longitude) or None if the address could not be found.
    '''
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    matches = data["result"]["addressMatches"]
    if matches:
        coords = matches[0]["coordinates"]
        print("COORDS FOUND")
        return coords["y"], coords["x"]  # lat, lng
    print("FAILURE")
    return None


# ------------------------------- API views -------------------------------- #

class RoommatePostViewSet(viewsets.ModelViewSet):
    """
    Receives all roommate post objects and returns JSON via serializer.
    """
    queryset = RoommatePost.objects.all()
    serializer_class = RoommatePostSerializer
