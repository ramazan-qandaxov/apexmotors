from django.db import models
from django.contrib.auth.models import User
from multiselectfield import MultiSelectField

class Car(models.Model):
    BRAND_CHOICES = [
        ('Aston Martin', 'Aston Martin'),
        ('Audi', 'Audi'),
        ('BMW', 'BMW'),
        ('Bugatti', 'Bugatti'),
        ('Ferrari', 'Ferrari'),
        ('Ford', 'Ford'),
        ('Lamborghini', 'Lamborghini'),
        ('Mercedes-Benz', 'Mercedes-Benz'),
        ('Porsche', 'Porsche'),
        ('Tesla', 'Tesla'),
        ('Toyota', 'Toyota'),
        ('Volkswagen', 'Volkswagen'),
        ('Other', 'Other')
    ]

    CATEGORY_CHOICES = [
        ('Hyper', 'Hyper'),
        ('Super', 'Super'),
        ('Sports', 'Sports'),
        ('Sedan', 'Sedan'),
        ('Luxury', 'Luxury'),
        ('Coupe', 'Coupe'),
        ('Roadster', 'Roadster'),
        ('Hatchback', 'Hatchback'),
        ('SUV', 'SUV'),
        ('Other', 'Other')
    ]

    NEW_USED_CHOICES = [
        ('New', 'New'),
        ('Used', 'Used')
    ]

    DRIVE_TRAIN = [
        ('FWD', 'FWD'),
        ('RWD', 'RDW'),
        ('AWD', 'AWD'),
        ('4WD', '4WD'),
        ('Other', 'Other')
    ]

    FUEL_TYPE = [
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
        ('Electric', 'Electric'),
        ('Hybrid', 'Hybrid'),
        ('Other', 'Other')
    ]

    TRANMISSION_TYPE = [
        ('Automatic', 'Automatic'),
        ('Manual', 'Manual'),
        ('Semi-Automatic', 'Semi-Automatic'),
        ('CVT', 'CVT'),
        ('Other', 'Other')
    ]

    COLOR_CHOICES = [
        ('Black', 'Black'),
        ('White', 'White'),
        ('Red', 'Red'),
        ('Blue', 'Blue'),
        ('Silver', 'Silver'),
        ('Gray', 'Gray'),
        ('Green', 'Green'),
        ('Yellow', 'Yellow'),
        ('Orange', 'Orange'),
        ('Purple', 'Purple'),
        ('Brown', 'Brown'),
        ('Other', 'Other')
    ]

    brand = models.CharField(max_length=50, choices=BRAND_CHOICES, default='Other')
    model = models.CharField(max_length=100, default='Unknown Model')
    description = models.TextField(default='No description available')
    price = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    new_or_used = models.CharField(max_length=10, choices=NEW_USED_CHOICES, default='New')

    year = models.IntegerField(default=2025)
    mileage = models.IntegerField(default=0)
    color = models.CharField(max_length=50, choices=COLOR_CHOICES, default='Other')
    available_colors = MultiSelectField(choices=COLOR_CHOICES, default=['Other'])

    engine = models.CharField(max_length=100, default='Unknown')
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPE, default='Other')
    drivetrain = models.CharField(max_length=50, choices=DRIVE_TRAIN, default='Other')
    horsepower = models.IntegerField(default=0)
    torque = models.IntegerField(default=0)
    transmission = models.CharField(max_length=50, choices=TRANMISSION_TYPE, default='Other')
    top_speed = models.IntegerField(default=0)
    acceleration = models.FloatField(default=0.0)  # 0-100 km/h in seconds
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cars', null=True, blank=True)

    document = models.FileField(upload_to='documents/', null=True, blank=True)

    

    def __str__(self):
        return f"{self.brand} {self.model}"

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/', default='defaults/default_car_image.jpg')

    def __str__(self):
        return f"Image for {self.car.brand} {self.car.model}"

class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"#{self.name}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    hashtags = models.ManyToManyField('Hashtag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Purchase(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
