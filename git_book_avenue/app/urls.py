from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('signup/', views.signup, name='signup'),
    
    # Cart URLs
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),

    # ... other urls ...
    path('profile/', views.profile, name='profile'),
    
    # ... about paths ...
    path('about/', views.about, name='about'),


    # ... other paths ...
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),

    path('student-offer/', views.student_offer, name='student_offer'),

    path('add-book/', views.add_book, name='add_book'),
    path('edit-book/<int:book_id>/', views.edit_book, name='edit_book'),
    path('publisher-dashboard/', views.publisher_dashboard, name='publisher_dashboard'),
    path('logout/', views.logout_view, name='logout')
]