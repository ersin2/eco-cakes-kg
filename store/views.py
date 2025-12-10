from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Cart, CartItem, Order, OrderProduct
from .forms import OrderForm
from django.core.exceptions import ObjectDoesNotExist
import urllib.parse 

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# ГЛАВНАЯ (МЕНЮ)
def home(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    cart_count = 0
    try:
        cart = Cart.objects.filter(cart_id=_cart_id(request))
        if cart.exists():
            cart_items = CartItem.objects.filter(cart=cart[:1])
            for item in cart_items:
                cart_count += item.quantity
    except:
        pass
    context = {'products': products, 'categories': categories, 'cart_count': cart_count}
    return render(request, 'store/home.html', context)

# О НАС
def about(request):
    cart_count = 0
    try:
        cart = Cart.objects.filter(cart_id=_cart_id(request))
        if cart.exists():
            cart_items = CartItem.objects.filter(cart=cart[:1])
            for item in cart_items:
                cart_count += item.quantity
    except:
        pass
    return render(request, 'store/about.html', {'cart_count': cart_count})

# ... (начало файла) ...

# ... (код в store/views.py до add_cart) ...

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        cart_item.save()
    
    # 🌟 ВОТ ИСПРАВЛЕНИЕ: Добавляем якорь (#menu-start) к текущему URL 🌟
    # Это заставит браузер прокрутиться к началу меню, если он сбросил позицию.
    # Если ты добавил товар из модального окна, HTTP_REFERER будет URL товара. 
    # Если ты добавил с главной, то это будет URL главной.
    
    current_url = request.META.get('HTTP_REFERER', '/')
    
    # Если мы находимся на главной странице, добавляем якорь
    if current_url.endswith('/') or current_url.endswith('/home/'):
         redirect_url = current_url + '#menu-start'
    else:
         redirect_url = current_url
         
    return redirect(redirect_url)


# ... (код в store/views.py после add_cart) ...
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        cart_item.save()
    
    # ИСПРАВЛЕНИЕ: БОЛЬШЕ НЕТ 'home'. Просто возвращаемся на предыдущую страницу.
    return redirect(request.META.get('HTTP_REFERER'))


# ... (остальной код views.py) ...
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        cart_item.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def cart(request):
    total = 0
    quantity = 0
    cart_items = None
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass
    return render(request, 'store/cart.html', {'total': total, 'quantity': quantity, 'cart_items': cart_items})

def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart')

def checkout(request):
    total = 0
    cart_items = None
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.address = form.cleaned_data['address']
            data.comment = form.cleaned_data['comment']
            data.payment_method = form.cleaned_data['payment_method']
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # ФОРМИРУЕМ СООБЩЕНИЕ (ИСПРАВЛЕНО: ДОБАВЛЕН СПИСОК ТОВАРОВ И ЦЕНА)
            pay_name = 'Наличные' if data.payment_method == 'cash' else 'QR / Перевод'
            
            wa_text = f"*НОВЫЙ ЗАКАЗ №{data.id}* 🎂\n\n"
            wa_text += f"👤 *Имя:* {data.first_name} {data.last_name}\n"
            wa_text += f"📞 *Тел:* {data.phone}\n"
            wa_text += f"📍 *Адрес:* {data.address}\n"
            wa_text += f"💳 *Оплата:* {pay_name}\n"
            wa_text += "------------------\n"
            
            wa_text += "*ТОВАРЫ:* \n"
            for item in cart_items:
                # 1. Сохраняем товар в базу
                OrderProduct.objects.create(
                    order=data, product=item.product, quantity=item.quantity,
                    product_price=item.product.price, ordered=True
                )
                # 2. Добавляем в текст WhatsApp
                wa_text += f"▫️ {item.product.name} (x{item.quantity}) = {item.sub_total()} с.\n"
            
            wa_text += "------------------\n"
            wa_text += f"🔥 *ИТОГО: {total} с.*\n"
            
            if data.comment:
                wa_text += f"\n💬 *Комментарий:* {data.comment}"

            # Чистим корзину и завершаем заказ
            CartItem.objects.filter(cart=cart).delete()
            data.is_ordered = True
            data.save()
            
            phone_number = "996704580285" 
            
            encoded_text = urllib.parse.quote(wa_text)
            whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_text}"
            return redirect(whatsapp_url)
    else:
        form = OrderForm()

    context = {'cart_items': cart_items, 'total': total, 'form': form}
    return render(request, 'store/checkout.html', context)