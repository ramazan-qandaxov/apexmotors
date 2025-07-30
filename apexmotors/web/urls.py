from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:pk>/', views.car_detail, name='car_detail'),
    path('about/', views.about, name='about'),
]
