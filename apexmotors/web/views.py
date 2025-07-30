from django.shortcuts import render, redirect, get_object_or_404
from .models import Car, CarImage
from .forms import CommentForm, CarForm
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.safestring import mark_safe


def home(request):
    cars = Car.objects.all()
    return render(request, 'home.html', {'cars': cars})

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    cars = Car.objects.filter(owner=user).order_by('-year')

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        images = request.FILES.getlist('image')  # multiple images from the HTML input

        if form.is_valid():
            car = form.save(commit=False)
            car.owner = user
            car.save()
            form.save_m2m()

            for img in images:
                CarImage.objects.create(car=car, image=img)

            return redirect('profile')
    else:
        form = CarForm()

    context = {
        'user': user,
        'cars': cars,
        'form': form
    }
    return render(request, 'profile.html', context)



def catalog(request):
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
