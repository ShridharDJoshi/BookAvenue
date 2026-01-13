from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Book(models.Model):
    category = models.ForeignKey(Category, related_name='books', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    publisher = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.FileField(upload_to='books/')
    stock = models.IntegerField(default=10) # Default 10 copies per book
    is_bestseller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def is_new(self):
        # Returns True if the book was added in the last 72 hours (3 days)
        # You can change 'days=3' to 'hours=24' if you prefer a shorter time.
        return self.created_at >= timezone.now() - timedelta(days=3)

    def __str__(self):
        return self.title

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100, default="")
    address = models.TextField(default="")
    city = models.CharField(max_length=100, default="")
    zip_code = models.CharField(max_length=20, default="")
    def __str__(self):
        return f"Order {self.id} by {self.user.username}"
    def get_total_cost(self):
        return sum(item.price * item.quantity for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.price * self.quantity
    
# --- Add this at the bottom of store/models.py ---

class Review(models.Model):
    book = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)  # 1 to 5
    comment = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_publisher = models.BooleanField(default=False)
    # NEW: Tracks if admin has approved them. 
    # Default is False so they start as "Pending".
    is_approved = models.BooleanField(default=False) 

    def __str__(self):
        return self.user.username