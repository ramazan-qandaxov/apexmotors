from django.contrib import admin
from .models import Car, CarImage, Hashtag, Comment

@admin.action(description='Duplicate selected car(s)')
def duplicate_cars(modeladmin, request, queryset):
    for obj in queryset:
        images = list(obj.images.all())  # assuming related_name='images' on CarImage
        obj.pk = None  # Create a new instance
        obj.model += " (Copy)"  # Optional: append "Copy" to model name
        obj.save()

        # Duplicate related CarImage instances
        for image in images:
            image.pk = None
            image.car = obj
            image.save()

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    fields = ('user', 'text', 'created_at')  # Display relevant fields
    readonly_fields = ('created_at',)  # Make created_at read-only

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'category', 'price', 'year', 'new_or_used')
    list_filter = ('category', 'new_or_used', 'year')
    search_fields = ('brand', 'model', 'description', 'color', 'engine')
    inlines = [CarImageInline, CommentInline]
    actions = [duplicate_cars]

@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)