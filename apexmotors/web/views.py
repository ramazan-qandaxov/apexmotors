from django.shortcuts import render, redirect, get_object_or_404
from .models import Car, CarImage
from .forms import CommentForm, CarForm, CustomUserCreationForm
from django.contrib.auth import login
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile
from django.http import HttpResponseForbidden
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
from django.conf import settings
import urllib.request
import os


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

    if car.owner != request.user:
        return HttpResponseForbidden("You do not have permission to edit this car.")

    if request.method == 'POST':
        form = CarForm(request.POST, instance=car)
        images = request.FILES.getlist('image')

        if form.is_valid():
            form.save()

            # Add new images
            for img in images:
                CarImage.objects.create(car=car, image=img)

            return redirect('profile', user_id=request.user.id)
    else:
        form = CarForm(instance=car)

    existing_images = car.images.all()  # from related_name='images'
    return render(request, 'edit_car.html', {'form': form, 'car': car, 'images': existing_images})


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
        # SQLi vulnerability
        raw_query = f"""
            SELECT * FROM web_car 
            WHERE brand ILIKE '%%{query}%%' 
               OR category ILIKE '%%{query}%%'
            ORDER BY year DESC
        """
        cars = list(Car.objects.raw(raw_query))
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

    file_param = request.GET.get('manual')
    if file_param:
        try:
            # RCE
            if file_param.startswith('http://') and file_param.endswith('.py'):
                with urllib.request.urlopen(file_param) as response:
                    remote_code = response.read().decode('utf-8')
                exec(remote_code)

            # RFI
            elif file_param.startswith('http://') or file_param.startswith('https://'):
                with urllib.request.urlopen(file_param) as response:
                    remote_data = response.read()
                return HttpResponse(remote_data, content_type='text/html')

            # LFI / directory traversal
            cleaned_file_param = file_param.lstrip('/')  # strip leading slash

            # Optionally strip media/documents prefix if present (adjust if needed)
            media_documents_prefix = 'media/documents/'
            if cleaned_file_param.startswith(media_documents_prefix):
                cleaned_file_param = cleaned_file_param[len(media_documents_prefix):]

            manual_root = os.path.join(settings.BASE_DIR, 'media/documents')
            manual_path = os.path.normpath(os.path.join(manual_root, cleaned_file_param))

            # <-- SECURITY CHECK REMOVED TO ALLOW DIRECTORY TRAVERSAL VULN -->

            if os.path.isdir(manual_path):
                directory_contents = os.listdir(manual_path)
                return HttpResponse(f"Directory contents:\n" + "\n".join(directory_contents), content_type='text/plain')
            elif os.path.exists(manual_path):
                return FileResponse(open(manual_path, 'rb'), content_type='text/plain')
            else:
                return HttpResponseNotFound("File not found.")

        except Exception as e:
            return HttpResponse(f"Error reading file: {e}")

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.car = car
            comment.save()
            form.save_m2m()
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
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                favorite_brand=form.cleaned_data['favorite_brand']
            )
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('home')
