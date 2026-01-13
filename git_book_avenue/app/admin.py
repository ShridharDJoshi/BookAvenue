from django.contrib import admin
from .models import Category, Book, Order, OrderItem, Review, UserProfile

# 1. NEW: Publisher Approval System
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_publisher', 'is_approved']
    list_filter = ['is_publisher', 'is_approved']
    actions = ['approve_publishers']

    def approve_publishers(self, request, queryset):
        queryset.update(is_approved=True)
    approve_publishers.short_description = "Approve selected publishers"

# 2. Existing Category Admin (Kept your slug logic)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

# 3. Existing Book Admin
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'price', 'category', 'publisher'] # Added publisher so you can see owner
    list_filter = ['publisher'] # Helpful to filter books by publisher

# 4. Existing Order Logic
class OrderItemInline(admin.TabularInline):
    model = OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'paid']
    inlines = [OrderItemInline]

# 5. Existing Review Admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'rating', 'created_at']