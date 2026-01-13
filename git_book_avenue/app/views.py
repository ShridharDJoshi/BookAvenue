from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Avg, Sum, Count
from django.contrib.auth.models import User
from django.db.models import Sum, F
# --- IMPORTS FROM YOUR APP ---
from .models import Book, Category, Order, OrderItem, Review, UserProfile
from .forms import ReviewForm, PublisherSignUpForm, BookForm
from django.contrib.auth import logout
from django.shortcuts import redirect
# --- 1. HOME & BROWSING ---

def home(request):
    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    
    books = Book.objects.all()
    
    # --- 1. SEARCH & FILTER LOGIC ---
    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        books = books.filter(category=category)

    categories = Category.objects.all()
    
    # --- 2. SMART RECOMMENDATION LOGIC ---
    recommended_books = []
    
    if request.user.is_authenticated:
        # A. Get all categories the user has purchased from
        # FIX: We use 'books__' (plural) because that matches your model relationship
        purchased_categories = Category.objects.filter(
            books__orderitem__order__user=request.user,
            books__orderitem__order__paid=True
        ).distinct()
        
        # B. Get IDs of books user has already bought (to exclude them)
        purchased_book_ids = Book.objects.filter(
            orderitem__order__user=request.user,
            orderitem__order__paid=True
        ).values_list('id', flat=True)

        # C. Loop through each category and get 4 random suggestions
        for cat in purchased_categories:
            # Get 4 random books from this category, EXCLUDING bought ones
            suggestions = Book.objects.filter(category=cat)\
                                      .exclude(id__in=purchased_book_ids)\
                                      .order_by('?')[:4]
            recommended_books.extend(suggestions)
            
        # Optional: Shuffle the final mix so genres are mixed together
        import random
        random.shuffle(recommended_books)

    # --- 3. FALLBACK (If not logged in, just show random 4 at bottom) ---
    footer_recommendations = Book.objects.order_by('?')[:4]

    return render(request, 'home.html', {
        'books': books, 
        'categories': categories,
        'recommended_books': recommended_books, 
        'footer_recommendations': footer_recommendations
    })

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # --- NEW: VERIFIED PURCHASE CHECK ---
    can_review = False
    if request.user.is_authenticated:
        # Check if the user has a PAID order containing this book
        can_review = OrderItem.objects.filter(
            order__user=request.user, 
            order__paid=True, 
            book=book
        ).exists()

    # 1. Handle Review Submission
    if request.method == 'POST' and request.user.is_authenticated:
        if can_review:  # Security: Only allow save if they actually bought it
            form = ReviewForm(request.POST)
            if form.is_valid():
                # Check if user already reviewed to prevent duplicates (Optional)
                if Review.objects.filter(user=request.user, book=book).exists():
                     return redirect('book_detail', pk=pk)
                
                review = form.save(commit=False)
                review.book = book
                review.user = request.user
                review.save()
                return redirect('book_detail', pk=pk)
        else:
            # If a non-buyer tries to force a POST request, just reload
            return redirect('book_detail', pk=pk)
    else:
        form = ReviewForm()

    # 2. Get Reviews & Average Rating
    reviews = book.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1) 

    related_books = Book.objects.filter(category=book.category).exclude(pk=pk)[:4]

    return render(request, 'book_detail.html', {
        'book': book, 
        'related_books': related_books,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'form': form,
        'can_review': can_review # Pass this flag to the template
    })

# --- 2. AUTHENTICATION (UPDATED FOR PUBLISHERS) ---

def signup(request):
    if request.method == 'POST':
        form = PublisherSignUpForm(request.POST)
        if form.is_valid():
            # 1. Create User
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # 2. Create UserProfile (Publisher or Customer)
            is_pub = form.cleaned_data.get('is_publisher')
            UserProfile.objects.create(user=user, is_publisher=is_pub)
            
            # 3. Log them in
            login(request, user)
            return redirect('home')
    else:
        form = PublisherSignUpForm()
    
    # Note: We use 'signup.html' now, consistent with custom forms
    return render(request, 'signup.html', {'form': form})

# --- 3. PUBLISHER DASHBOARD (ADD / EDIT BOOKS) ---

@login_required
def add_book(request):
    # Security: Only Publishers can access this
    try:
        if not request.user.userprofile.is_publisher:
            return redirect('home')
    except:
        return redirect('home')

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.publisher = request.user  # Assign current user as publisher
            book.save()
            return redirect('home')
    else:
        form = BookForm()
    
    return render(request, 'add_book.html', {'form': form})

@login_required
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    # Security: Only the owner (Publisher) can edit their book
    if book.publisher != request.user:
        return redirect('home')

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_detail', pk=book.id)
    else:
        form = BookForm(instance=book)
    
    return render(request, 'add_book.html', {'form': form, 'is_edit': True})

# --- 4. CART LOGIC ---

def add_to_cart(request, pk):
    cart = request.session.get('cart', {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session['cart'] = cart
    return redirect('cart_view')

def remove_from_cart(request, pk):
    cart = request.session.get('cart', {})
    if str(pk) in cart:
        del cart[str(pk)]
    request.session['cart'] = cart
    return redirect('cart_view')

def cart_view(request):
    cart = request.session.get('cart', {})
    books_in_cart = []
    total_price = 0
    
    for book_id, quantity in cart.items():
        # Handle dictionary vs int quantity format safely
        qty = quantity['quantity'] if isinstance(quantity, dict) else quantity
        
        try:
            book = Book.objects.get(id=book_id)
            total = book.price * qty
            total_price += total
            books_in_cart.append({'book': book, 'quantity': qty, 'total_price': total})
        except Book.DoesNotExist:
            continue
            
    return render(request, 'cart.html', {'cart_items': books_in_cart, 'total_price': total_price})

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart_view')

    # --- 1. POST LOGIC (Processing the Order) ---
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')

        order = Order.objects.create(
            user=request.user, 
            paid=True,
            full_name=full_name,
            address=address,
            city=city,
            zip_code=zip_code
        )
        
        total_price = 0
        
        for book_id, item_data in cart.items():
            try:
                book = Book.objects.get(id=book_id)
                quantity = item_data['quantity'] if isinstance(item_data, dict) else item_data

                if book.stock >= quantity:
                    book.stock -= quantity
                    book.save()
                    OrderItem.objects.create(order=order, book=book, price=book.price, quantity=quantity)
                    total_price += book.price * quantity
            except Book.DoesNotExist:
                continue

        order.total_price = total_price
        order.save()
        request.session['cart'] = {}
        return redirect('profile') 

    # --- 2. GET LOGIC (Displaying the Page) ---
    # We must calculate the totals here so the user can see them BEFORE clicking submit
    cart_items = []
    total_price = 0

    for book_id, item_data in cart.items():
        try:
            book = Book.objects.get(id=book_id)
            quantity = item_data['quantity'] if isinstance(item_data, dict) else item_data
            
            total = book.price * quantity
            total_price += total
            
            cart_items.append({
                'book': book,
                'quantity': quantity,
                'total': total
            })
        except Book.DoesNotExist:
            continue

    # Pass these variables to the template
    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'checkout.html', context)

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'profile.html', {'orders': orders})

# --- 5. MISC PAGES ---

def about(request):
    return render(request, 'about.html')

def student_offer(request):
    error_message = None
    if request.method == "POST":
        error_message = "Please enter a valid Student ID."
    return render(request, 'student_offer.html', {'error_message': error_message})

@staff_member_required
def manager_dashboard(request):
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_books = Book.objects.count()
    
    revenue_data = OrderItem.objects.filter(order__paid=True).aggregate(Sum('price'))
    total_revenue = revenue_data['price__sum'] or 0
    
    recent_orders = Order.objects.order_by('-created_at')[:5]
    popular_books = Book.objects.annotate(num_sold=Count('orderitem')).order_by('-num_sold')[:5]

    context = {
        'total_orders': total_orders,
        'total_users': total_users,
        'total_books': total_books,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'popular_books': popular_books,
    }
    return render(request, 'dashboard.html', context)

@login_required
def publisher_dashboard(request):
    # 1. Security Check: Must be a publisher
    try:
        profile = request.user.userprofile
        if not profile.is_publisher:
            return redirect('home')
    except:
        return redirect('home')

    # 2. Approval Check: If not approved, show "Pending" screen
    if not profile.is_approved:
        return render(request, 'publisher_pending.html')

    # 3. Get Publisher's Books
    my_books = Book.objects.filter(publisher=request.user).order_by('-created_at')

    # 4. Calculate Stats (Revenue & Sales)
    # We look at OrderItems related to this publisher's books
    publisher_items = OrderItem.objects.filter(book__publisher=request.user, order__paid=True)
    
    total_sales_count = publisher_items.count()
    
    # Calculate total revenue (Sum of price * quantity)
    # Note: We calculate this manually or using aggregation
    revenue_data = publisher_items.aggregate(total=Sum(F('price') * F('quantity')))
    total_revenue = revenue_data['total'] or 0

    # 5. Calculate Average Rating across all their books
    avg_rating_data = Review.objects.filter(book__publisher=request.user).aggregate(Avg('rating'))
    overall_rating = avg_rating_data['rating__avg'] or 0
    overall_rating = round(overall_rating, 1)

    context = {
        'books': my_books,
        'total_revenue': total_revenue,
        'total_sales': total_sales_count,
        'overall_rating': overall_rating,
    }
    return render(request, 'publisher_dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('home')