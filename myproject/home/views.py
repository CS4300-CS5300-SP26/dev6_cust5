from django.shortcuts import render
from .models import Property
from .rentcast_api import get_properties


def index(request):

    # Start with all database properties
    properties = Property.objects.all()

    # Get search parameters
    location = request.GET.get("location", "").strip()
    listing_type = request.GET.get("intent", "").strip()
    property_type = request.GET.get("type", "").strip()
    price_range = request.GET.get("budget", "").strip()

    # Container for API results
    api_properties = []

    # -------- Location Filter --------
    if location:
        properties = properties.filter(location__icontains=location)

    # -------- RentCast API Call --------
    if location:
        try:
            api_properties = get_properties(location)
            print("API Results:", api_properties)  # Debug check
        except Exception as e:
            print("API Error:", e)
            api_properties = []

    # -------- Listing Type Filter --------
    if listing_type in ["rent", "buy"]:
        properties = properties.filter(listing_type=listing_type)

    # -------- Property Type Filter --------
    if property_type and property_type.lower() != "any type":
        properties = properties.filter(property_type=property_type.lower())

    # -------- Price Range Filter --------
    if price_range and price_range != "any":
        try:
            min_price, max_price = map(int, price_range.split("-"))
            properties = properties.filter(price__gte=min_price, price__lte=max_price)
        except ValueError:
            pass

    # Count database results
    result_count = properties.count()

    # Send everything to template
    context = {
        "properties": properties,
        "api_properties": api_properties,
        "selected_location": location,
        "selected_intent": listing_type,
        "selected_type": property_type,
        "selected_budget": price_range,
        "result_count": result_count,
    }

    return render(request, "bear_estate_homepage.html", context)