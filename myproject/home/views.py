from django.shortcuts import render
from .models import Property


def index(request):
    properties = Property.objects.all()

    location = request.GET.get("location", "").strip()
    listing_type = request.GET.get("intent", "").strip()
    property_type = request.GET.get("type", "").strip()
    budget = request.GET.get("budget", "").strip()

    if location:
        properties = properties.filter(location__icontains=location)

    if listing_type in ["rent", "buy"]:
        properties = properties.filter(listing_type=listing_type)

    if property_type and property_type.lower() != "any type":
        properties = properties.filter(property_type=property_type.lower())

    if budget and budget != "any":
        try:
            min_price, max_price = budget.split("-")
            properties = properties.filter(price__gte=min_price, price__lte=max_price)
        except ValueError:
            pass

    context = {
        "properties": properties,
        "selected_location": location,
        "selected_intent": listing_type,
        "selected_type": property_type,
        "selected_budget": budget,
    }

    return render(request, "bear_estate_homepage.html", context)