from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/<int:user_id>', views.profile, name='profile'),
    path('car/add/', views.add_car, name='add_car'),
    path('car/edit/<int:car_id>/', views.edit_car, name='edit_car'),
    path('car/delete/<int:car_id>/', views.delete_car, name='delete_car'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:pk>/', views.car_detail, name='car_detail'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
]
