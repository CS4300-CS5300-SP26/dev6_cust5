from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from home.forms import CustomRegisterForm

def index(request):
    context = {}
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
    return render(request, 'bear_estate_homepage.html', context)

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