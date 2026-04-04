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

#--------------------------------- MAP ------------------------------------------#

# Map View
def map_view(request):
    '''
    Parameters: request
    Handles user input from map page or landing page. Gets coordinates for addresses from RentCast API or geocoding if necessary. Passes coordinates to template for map display.
    Returns: Displays map view
    '''
    
    map_properties = []              

    # Handles requests
    # 2 instances of input are gotten (City, State).

    # Read params from POST (search bar)
    if request.method == 'POST':
        city  = request.POST.get('city', '').strip().title()         # strips whitespace and capitalizes first letter of each word (for cities with 2 words, e.g Castle Rock, CO)
        state = request.POST.get('state', '').strip()               # strips whitespace
        print("FROM POST:", str(city), str(state))                 # debugging
    
    # Reads params from GET (redirect from landing page)
    elif request.method == 'GET':
        city  = request.GET.get('city', '').strip().title()           # strips whitespace and capitalizes first letter of each word
        state = request.GET.get('state', '').strip().upper()          # strips whitespace and capitalizes state (assuming use of state abbreviations)
        print("FROM GET:", city, state)        # debugging

    # User input not given
    else:
        city  = ''
        state = ''
        
    # if input was given
    if city and state:
        # Concatenates city and state for API call
        location_str = f"{city}, {state}"

        # Fetch filtered listings from RentCast
        rentcast_results = fetch_filtered_properties(location_str, listing_type, property_type, price_range)

        # Loops through results from API
        for prop in rentcast_results:
            # Use coordinates from RentCast if available, otherwise geocode the address
            lat = prop.get("latitude")
            lng = prop.get("longitude")

            # Geocodes address if applicable
            if not lat or not lng:
                address = prop.get("formattedAddress")
                if address:
                    coords = geocode_residential(address)
                    if coords:
                        lat, lng = coords
            # END OF GEOCODING

            # Creates entry for map context (for map markers)
            if lat and lng:
                map_properties.append({
                    'latitude': lat,
                    'longitude': lng,
                    'location': prop.get("formattedAddress", "Unknown address"),
                    'property_type': prop.get("propertyType", "Unknown type"),
                    'rent': prop.get("price"),
                    'beds': prop.get("bedrooms"),
                    'baths': prop.get("bathrooms"),
                    'sqft': prop.get("squareFootage"),
                })
            # END OF MAP ENTRY
        # END OF RENTCAST FOR
    # END OF USER INPUT HANDLING
                 
    # No user input   
    else:
        # Defaults context to empty
        all_properties = Property.objects.exclude(latitude=None, longitude=None)
        map_properties = list(all_properties.values('latitude', 'longitude', 'location'))

    context = {
        'properties': json.dumps(map_properties),
        'properties_count': len(map_properties),
        'city': city,
        'state': state,
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
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    matches = data["result"]["addressMatches"]
    if matches:
        coords = matches[0]["coordinates"]
        return coords["y"], coords["x"]  # lat, lng
    return None

# FILTER FUNCTION FOR MAP VIEW (taken from index)
def fetch_filtered_properties(location, listing_type=None, property_type=None, price_range=None):
    '''
    Parameters: a location, listing type, property, type and price range
    Will filter out properties from RentCast API with the filters passed in.
    Return: Returns a list of RentCast properties
    '''
    min_price, max_price = None, None
    if price_range and price_range != "any":
        try:
            min_price, max_price = map(int, price_range.split("-"))
        except ValueError:
            pass

    try:
        return get_properties(
            location,
            property_type=property_type,
            min_price=min_price,
            max_price=max_price,
        )
    except Exception as e:
        print("API Error:", e)
        return []

# ------------------------ HOME PAGE -------------------------- 

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
    if location:
        parts = location.split(",")
        city  = parts[0].strip() if len(parts) > 0 else ''
        state = parts[1].strip() if len(parts) > 1 else ''

    listing_type = request.GET.get("mode", "").strip()
    property_type = request.GET.get("type", "").strip()
    price_range = request.GET.get("budget", "").strip()

    ''' SEARCHES PROPERTY MODEL
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
    '''
    if location:
        # Redirects to map page. Passes in parameters for 
        return redirect(f"/map/?city={city}&state={state}&intent={listing_type}&type={property_type}&budget={price_range}")
    
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

# ------------------------------- API views -------------------------------- #

class RoommatePostViewSet(viewsets.ModelViewSet):
    """
    Receives all roommate post objects and returns JSON via serializer.
    """
    queryset = RoommatePost.objects.all()
    serializer_class = RoommatePostSerializer
