from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

# Create your views here.
def index(request):
    return render(request, 'index.html')

def search(request):
    return render(request, 'search.html')