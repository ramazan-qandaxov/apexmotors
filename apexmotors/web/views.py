from django.shortcuts import render, redirect, get_object_or_404
from .models import Car, CarImage
from .forms import CommentForm, CarForm
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile
from django.http import HttpResponseForbidden


def home(request):
    cars = Car.objects.all()
    return render(request, 'home.html', {'cars': cars})

# IDOR vulnerability

@login_required
def profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    cars = Car.objects.filter(owner=user).order_by('-year')

    try:
        user_profile = user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = None

    context = {
        'user': user,
        'cars': cars,
        'profile': user_profile
    }

    return render(request, 'profile.html', context)

@login_required
def add_car(request):
    """
    Allow authenticated users to add a car for sale, including multiple images.
    """
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        images = request.FILES.getlist('image')  # Handles multiple uploaded images

        if form.is_valid():
            car = form.save(commit=False)
            car.owner = request.user  # Associate car with the current user
            car.save()
            form.save_m2m()  # Save many-to-many relationships like available_colors

            # Save each uploaded image linked to the car
            for img in images:
                CarImage.objects.create(car=car, image=img)

            return redirect('profile', user_id=request.user.id)  # Redirect to the user's profile after adding
    else:
        form = CarForm()

    return render(request, 'add_car.html', {'form': form})

@login_required
def edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    # Access control: only owner can edit
    if car.owner != request.user:
        return HttpResponseForbidden("You do not have permission to edit this car.")

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            return redirect('profile', user_id=request.user.id)
    else:
        form = CarForm(instance=car)

    return render(request, 'edit_car.html', {'form': form, 'car': car})

@login_required
def delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    # Access control: only owner can delete
    if car.owner != request.user:
        return HttpResponseForbidden("You do not have permission to delete this car.")

    if request.method == 'POST':
        car.delete()
        return redirect('profile', user_id=request.user.id)

    return render(request, 'confirm_delete.html', {'car': car})

def catalog(request):
    query = request.GET.get("q")
    
    if query:
        # VULNERABLE TO SQL INJECTION — FOR DEMO PURPOSES ONLY
        raw_query = f"""
            SELECT * FROM web_car 
            WHERE brand ILIKE '%%{query}%%' 
               OR category ILIKE '%%{query}%%'
            ORDER BY year DESC
        """
        cars = list(Car.objects.raw(raw_query))  # convert RawQuerySet to list
    else:
        cars = Car.objects.all().order_by('-year')
    
    paginator = Paginator(cars, 12)
    page_number = request.GET.get('page', 1)

    try:
        page_number = int(page_number)
        page_obj = paginator.page(page_number)
    except (ValueError, EmptyPage):
        raise Http404("Page not found.")

    context = {'page_obj': page_obj}
    return render(request, 'cars.html', context)

def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    comments = car.comments.select_related('user').prefetch_related('hashtags').all()

    for comment in comments:
        comment.text = mark_safe(comment.text)

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.car = car
            comment.save()
            form.save_m2m()  # Save many-to-many relationships (hashtags)
            return redirect('car_detail', pk=pk)
    else:
        form = CommentForm()

    return render(request, 'detail.html', {
        'car': car,
        'comments': comments,
        'form': form
    })


def about(request):
    return render(request, 'about.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')  # or 'main'
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('login')
