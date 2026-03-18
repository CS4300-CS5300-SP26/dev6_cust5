from django.shortcuts import render
from .models import RoommatePost
from rest_framework import viewsets
from .serializers import RoommatePostSerializer
from .forms import CustomRegisterForm, RoommatePostForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from .models import Property
from .rentcast_api import get_properties
from django.contrib.auth.decorators import login_required
from django.utils import timezone
#-------------------------------HTML views--------------------------------#
# Home page
def search(request):
    return render(request, "search.html")
    
#Search for Roommates
def roommate_list(request):
    posts = RoommatePost.objects.all().order_by('-date')
    return render(request, 'roommate_postings_view.html', {'posts': posts})

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

@login_required
def roommate_close(request, post_id):
    post = get_object_or_404(RoommatePost, id=post_id, user=request.user)
    if request.method == 'POST':
        post.status = 'closed'
        post.save()
        return redirect('roommate_list')
    return redirect('roommate_list')

@login_required
def roommate_delete(request, post_id):
    post = get_object_or_404(RoommatePost, id=post_id, user=request.user)  # ensures only owner can delete
    if request.method == 'POST':
        post.delete()
        return redirect('roommate_list')
    return redirect('roommate_list')
#-------------------------------API views--------------------------------#
# Roommate Post API
class RoommatePostViewSet(viewsets.ModelViewSet):
    '''
    Recieves all the roommate post objects. Calls the serializer.
    Displays the data in json format.
    '''
    queryset = RoommatePost.objects.all()
    serializer_class = RoommatePostSerializer

#------------------------------------------------------------------------#
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
    listing_type = request.GET.get("intent", "").strip()
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
        #properties = properties.filter(location__icontains=location)
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
