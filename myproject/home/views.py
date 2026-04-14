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
import pyotp
import qrcode, io, base64


# ---------------------- NEIGHBORHOOD MOCK DATA ---------------------- #

NEIGHBORHOOD_COSTS = {
    
    ("Austin", "TX"): {
    "Downtown": {
        "monthly_utilities": 190,
        "monthly_services": 85,
        "nearby_amenities": ["Gym", "Restaurants", "Transit", "Coffee Shop", "Grocery Store"],
    },
    "University Area": {
        "monthly_utilities": 170,
        "monthly_services": 70,
        "nearby_amenities": ["Gym", "Transit", "Coffee Shop", "Restaurants"],
    },
    "Default": {
        "monthly_utilities": 160,
        "monthly_services": 65,
        "nearby_amenities": ["Grocery Store", "Gym", "Restaurants", "Transit", "Coffee Shop"],
    },
},
    ("Boulder", "CO"): {
        "Downtown": {
            "monthly_utilities": 210,
            "monthly_services": 95,
            "nearby_amenities": ["Grocery Store", "Gym", "Bus Stop", "Coffee Shop"],
        },
        "University Hill": {
            "monthly_utilities": 180,
            "monthly_services": 70,
            "nearby_amenities": ["Campus", "Restaurants", "Transit"],
        },
        "Default": {
            "monthly_utilities": 160,
            "monthly_services": 60,
            "nearby_amenities": ["Grocery Store", "Gym", "Restaurants", "Transit", "Coffee Shop"],
        },
    },
    ("Denver", "CO"): {
        "Downtown": {
            "monthly_utilities": 220,
            "monthly_services": 120,
            "nearby_amenities": ["Transit", "Gym", "Grocery", "Restaurants", "Coffee Shop"],
        },
        "Capitol Hill": {
            "monthly_utilities": 175,
            "monthly_services": 80,
            "nearby_amenities": ["Transit", "Coffee Shops", "Grocery", "Restaurants", "Gym"],
        },
        "Default": {
            "monthly_utilities": 165,
            "monthly_services": 75,
            "nearby_amenities": ["Grocery Store", "Gym", "Restaurants", "Transit", "Coffee Shop"],
        },
    },
}


def get_neighborhood_profile(city, state, address):
    city_data = NEIGHBORHOOD_COSTS.get((city, state), {})
    address_lower = (address or "").lower()

    if "downtown" in address_lower:
        neighborhood = "Downtown"
    elif "hill" in address_lower:
        neighborhood = "University Hill" if city == "Boulder" else "Capitol Hill"
    else:
        neighborhood = f"{city} Area"

    profile = city_data.get(neighborhood)
    if not profile:
        profile = city_data.get(
            "Default",
            {
                "monthly_utilities": 150,
                "monthly_services": 50,
                "nearby_amenities": [],
            },
        )

    return neighborhood, profile


# ---------------------- AGENT ADVERTISING HELPERS ---------------------- #

def score_listing_for_agent(property_data, user_preferences):
    """
    Scores a property based on the user's filters/search choices.
    Higher score = better curated agent recommendation.
    """
    score = 0

    rent = property_data.get("rent") or 0
    total_cost = property_data.get("total_monthly_cost") or 0
    listing_property_type = (property_data.get("property_type") or "").strip()
    amenities = property_data.get("nearby_amenities", [])

    budget = user_preferences.get("budget")
    desired_type = user_preferences.get("property_type")
    desired_amenity = user_preferences.get("amenity")
    listing_type = user_preferences.get("listing_type")

    # Stronger property type match
    if desired_type and listing_property_type == desired_type:
        score += 5

    # Stronger amenity match
    if desired_amenity and desired_amenity.lower() != "any":
        if any(desired_amenity.lower() in amenity.lower() for amenity in amenities):
            score += 8

    # Budget match + reward cheaper listings inside the selected range
    if budget and budget != "any":
        try:
            min_price, max_price = map(int, budget.split("-"))
            if min_price <= rent <= max_price:
                score += 6
                score += max(0, (max_price - rent) // 100)
        except ValueError:
            pass

    # Favor lower total monthly cost
    if total_cost:
        if total_cost < 1200:
            score += 6
        elif total_cost < 1600:
            score += 4
        elif total_cost < 2000:
            score += 2

    # Ownership-friendly preference for buy searches
    if listing_type == "for_sale" and listing_property_type in ["Condo", "Townhouse", "House"]:
        score += 3

    return score


def generate_agent_message(user_preferences, recommended_properties):
    """
    Creates a short message explaining why the agent picks were selected.
    """
    city = user_preferences.get("city") or "this area"
    listing_type = user_preferences.get("listing_type") or ""
    amenity = user_preferences.get("amenity") or "your preferred amenities"

    if not recommended_properties:
        return "No curated recommendations are available yet for your current filters."

    if listing_type == "for_rent":
        return f"Based on your rental search in {city}, these agent picks best match your budget, property preferences, and nearby amenities like {amenity}."
    elif listing_type == "for_sale":
        return f"Based on your home-buying search in {city}, these curated listings are strong matches for your selected filters and neighborhood preferences."
    else:
        return f"Based on your search in {city}, these curated listings best match your filters, searched amenities, and likely housing needs."


def get_buyer_readiness_message(user_preferences):
    """
    Optional message for renters who may also be good candidates to buy.
    """
    listing_type = user_preferences.get("listing_type")
    budget = user_preferences.get("budget")

    if listing_type == "for_rent" and budget in ["1400-2000", "2000-999999"]:
        return (
            "Agent Insight: Based on your budget, you may also be a strong candidate "
            "for entry-level homeownership options in this area. A real estate agent "
            "could help you compare renting versus buying."
        )

    return ""


# ------------------------------- HTML views -------------------------------- #

# Home page
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


# --------------------------------- MAP ------------------------------------------ #

# Map View
def map_view(request):
    """
    Handles user input from map page or landing page. Gets coordinates for addresses
    from RentCast API or geocoding if necessary. Passes coordinates to template for map display.
    Also builds curated agent recommendations from user filters and matched listings.
    """

    map_properties = []
    recommended_properties = []
    agent_message = ""
    buyer_readiness_message = ""

    # Default values so nothing breaks
    city = ''
    state = ''
    listing_type = ''
    property_type = ''
    price_range = ''
    sort_by = ''
    amenity_filter = ''

    # Read params from POST (search bar)
    if request.method == 'POST':
        city = request.POST.get('city', '').strip().title()
        state = request.POST.get('state', '').strip().upper()
        listing_type = request.POST.get('intent', '').strip()
        property_type = request.POST.get('type', '').strip()
        price_range = request.POST.get('budget', '').strip()
        sort_by = request.POST.get('sort', '').strip()
        amenity_filter = request.POST.get('amenity', '').strip()
        print("FROM POST:", city, state)

    # Read params from GET (redirect from landing page)
    elif request.method == 'GET':
        city = request.GET.get('city', '').strip().title()
        state = request.GET.get('state', '').strip().upper()
        listing_type = request.GET.get('intent', '').strip()
        property_type = request.GET.get('type', '').strip()
        price_range = request.GET.get('budget', '').strip()
        sort_by = request.GET.get('sort', '').strip()
        amenity_filter = request.GET.get('amenity', '').strip()
        print("FROM GET:", city, state)

    # If input was given
    if city and state:
        location_str = f"{city}, {state}"

        # Fetch filtered listings from RentCast
        rentcast_results = fetch_filtered_properties(
            location_str,
            listing_type,
            property_type,
            price_range
        )

        # Loop through results from API
        for prop in rentcast_results:
            # Use coordinates from RentCast if available, otherwise geocode the address
            lat = prop.get("latitude")
            lng = prop.get("longitude")

            address = prop.get("formattedAddress", "Unknown address")

            # Geocode address if applicable
            if not lat or not lng:
                if address:
                    coords = geocode_residential(address)
                    if coords:
                        lat, lng = coords

            # Create entry for map context
            if lat and lng:
                neighborhood, profile = get_neighborhood_profile(city, state, address)

                rent = prop.get("price") or 0
                monthly_utilities = profile["monthly_utilities"]
                monthly_services = profile["monthly_services"]
                nearby_amenities = profile["nearby_amenities"]
                total_monthly_cost = rent + monthly_utilities + monthly_services

                map_properties.append({
                    'latitude': lat,
                    'longitude': lng,
                    'location': address,
                    'property_type': prop.get("propertyType", "Unknown type"),
                    'rent': rent,
                    'beds': prop.get("bedrooms"),
                    'baths': prop.get("bathrooms"),
                    'sqft': prop.get("squareFootage"),
                    'neighborhood': neighborhood,
                    'monthly_utilities': monthly_utilities,
                    'monthly_services': monthly_services,
                    'nearby_amenities': nearby_amenities,
                    'total_monthly_cost': total_monthly_cost,
                })

        # Optional amenity filter
        if amenity_filter and amenity_filter.lower() != "any":
            map_properties = [
                p for p in map_properties
                if any(
                    amenity_filter.lower() in amenity.lower()
                    for amenity in p.get("nearby_amenities", [])
                )
            ]

        # Optional sorting
        if sort_by == 'rent_asc':
            map_properties.sort(key=lambda p: p.get('rent') or 0)
        elif sort_by == 'rent_desc':
            map_properties.sort(key=lambda p: p.get('rent') or 0, reverse=True)
        elif sort_by == 'total_cost_asc':
            map_properties.sort(key=lambda p: p.get('total_monthly_cost') or 0)
        elif sort_by == 'total_cost_desc':
            map_properties.sort(key=lambda p: p.get('total_monthly_cost') or 0, reverse=True)

        # ---------------- AGENT ADVERTISING / CURATED PICKS ---------------- #

        user_preferences = {
            "city": city,
            "state": state,
            "listing_type": listing_type,
            "property_type": property_type,
            "budget": price_range,
            "amenity": amenity_filter,
            "sort_by": sort_by,
        }

        for prop in map_properties:
            prop["agent_score"] = score_listing_for_agent(prop, user_preferences)

        recommended_properties = sorted(
            map_properties,
            key=lambda p: p.get("agent_score", 0),
            reverse=True
        )[:3]

        agent_message = generate_agent_message(user_preferences, recommended_properties)
        buyer_readiness_message = get_buyer_readiness_message(user_preferences)

    else:
        # Defaults context to empty / existing DB properties
        all_properties = Property.objects.exclude(latitude=None, longitude=None)
        map_properties = list(all_properties.values('latitude', 'longitude', 'location'))

    context = {
        'properties': json.dumps(map_properties),
        'properties_count': len(map_properties),
        'city': city,
        'state': state,
        'listing_type': listing_type,
        'property_type': property_type,
        'price_range': price_range,
        'sort_by': sort_by,
        'amenity_filter': amenity_filter,
        'recommended_properties': recommended_properties,
        'agent_message': agent_message,
        'buyer_readiness_message': buyer_readiness_message,
    }
    return render(request, 'map.html', context)


# Geocode helper function
def geocode_residential(address):
    """
    Uses the US Census Bureau API to convert an address to coordinates.
    Returns a tuple of (latitude, longitude) or None if the address could not be found.
    """
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
    """
    Parameters: a location, listing type, property type and price range
    Will filter out properties from RentCast API with the filters passed in.
    Return: Returns a list of RentCast properties
    """
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


# ------------------------ HOME PAGE -------------------------- #

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
    city = ''
    state = ''

    if location:
        parts = location.split(",")
        city = parts[0].strip() if len(parts) > 0 else ''
        state = parts[1].strip() if len(parts) > 1 else ''

    listing_type = request.GET.get("mode", "").strip()
    property_type = request.GET.get("type", "").strip()
    price_range = request.GET.get("budget", "").strip()

    """
    SEARCHES PROPERTY MODEL
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
    """

    if location:
        return redirect(
            f"/map/?city={city}&state={state}&intent={listing_type}&type={property_type}&budget={price_range}"
        )

    return render(request, "bear_estate_homepage.html", context)


# User Register
def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('2fa_setup')
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


# Two-Factor Auth
@login_required
def setup_2fa(request):
    """
    GET -> render setup page with both TOTP and email options.
    POST method=totp_verify -> confirm TOTP code, save TOTP as 2FA method.
    POST method=email_send -> generate + email a 6-digit code, re-render for verify step.
    POST method=email_verify -> confirm emailed code, save email as 2FA method.
    """
    import random
    from django.core.mail import send_mail

    def _totp_context():
        secret = request.session.get('totp_secret') or pyotp.random_base32()
        request.session['totp_secret'] = secret
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=request.user.username, issuer_name='BearEstate'
        )
        qr_img = qrcode.make(totp_uri)
        buf = io.BytesIO()
        qr_img.save(buf, format='PNG')
        return {
            'qr_code': base64.b64encode(buf.getvalue()).decode(),
            'short_key': ' '.join(secret[i:i+4] for i in range(0, len(secret), 4)),
            'totp_secret': secret,
        }

    if request.method == 'POST':
        method = request.POST.get('method')

        # TOTP verify
        if method == 'totp_verify':
            secret = request.session.get('totp_secret', '')
            if secret and pyotp.TOTP(secret).verify(request.POST.get('otp_code', '')):
                p = request.user.profile
                p.totp_secret = secret
                p.totp_enabled = True
                p.two_fa_method = 'totp'
                p.save()
                return redirect('bear_estate_homepage')
            ctx = _totp_context()
            ctx['totp_error'] = 'Incorrect code — please try again.'
            return render(request, '2fa_setup.html', ctx)

        # Send code to Email
        if method == 'email_send':
            email = request.user.email
            if not email:
                ctx = _totp_context()
                ctx['email_error'] = 'No email address on your account. Please update your profile first.'
                return render(request, '2fa_setup.html', ctx)
            code = str(random.randint(100000, 999999))
            request.session['email_otp'] = code
            send_mail(
                subject='Your BearEstate verification code',
                message=f'Your one-time code is: {code}\n\nIt expires in 10 minutes.',
                from_email='noreply@bearestate.me',
                recipient_list=[email],
                fail_silently=False,
            )
            ctx = _totp_context()
            ctx['email_sent'] = True
            ctx['email_address'] = email
            return render(request, '2fa_setup.html', ctx)

        # Email Verify
        if method == 'email_verify':
            entered = request.POST.get('email_code', '').strip()
            stored = request.session.get('email_otp', '')
            if entered == stored and stored:
                p = request.user.profile
                p.totp_enabled = True
                p.two_fa_method = 'email'
                p.save()
                del request.session['email_otp']
                return redirect('bear_estate_homepage')
            ctx = _totp_context()
            ctx['email_sent'] = True
            ctx['email_address'] = request.user.email
            ctx['email_error'] = 'Incorrect code — please try again.'
            return render(request, '2fa_setup.html', ctx)

    return render(request, '2fa_setup.html', _totp_context())