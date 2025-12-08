from django.shortcuts import render
from .models import Product
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, CartItem, Order, OrderProduct, Category
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from urllib.parse import quote
from django.contrib import messages
# Вспомогательная функция (поэтому начинается с подчеркивания)
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        request.session.create()
        cart = request.session.session_key
    return cart
# В начале файла добавь: # <--- Добавь Category
def home(request):
    # Получаем категорию из URL (если нажали на кнопку)
    category_slug = request.GET.get('category')
    
    if category_slug:
        products = Product.objects.filter(category__slug=category_slug, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)
        
    # Получаем ВСЕ категории для кнопок меню
    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories, # <--- Передаем их в шаблон
    }
    return render(request, 'store/home.html', context)
def add_cart(request, product_id):
    # 1. Получаем сам товар по ID (или ошибка 404, если товара нет)
    product = get_object_or_404(Product, id=product_id)
    print("------------------------------------------------")
    print(f"КЛИК ПО КНОПКЕ! Товар ID: {product_id}")
    print(f"Сессия пользователя: {_cart_id(request)}")
    print("------------------------------------------------")
    
    try:
        # 2. Ищем корзину этого пользователя (по session_id)
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        # Если корзины нет - создаем новую
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
        cart.save()

    try:
        # 3. Ищем, есть ли уже этот товар в корзине
        cart_item = CartItem.objects.get(product=product, cart=cart)
        # Если есть - увеличиваем количество на 1
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        # Если нет - создаем новый запись (1 шт)
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart
        )
        cart_item.save()
    
    # 4. Возвращаем пользователя обратно на главную (пока что)
    # ... (код добавления товара выше) ...
    
    # 👇 ВМЕСТО redirect('cart') ПИШЕМ ЭТО:
    
    # 1. Показываем всплывающее сообщение
    messages.success(request, f'Товар добавлен в корзину! 🍰')
    
    # 2. Возвращаем пользователя на ТУ ЖЕ страницу, где он был
    return redirect(request.META.get('HTTP_REFERER', 'store'))
# Create your views here.

def cart(request, total=0, quantity=0, cart_items=None):

    try:
        # 1. Ищем корзину по сессии
        cart = Cart.objects.get(cart_id=_cart_id(request))
        # 2. Достаем активные товары из этой корзины
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        # 3. Считаем сумму и количество
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass # Если корзины нет - просто отдадим пустой список

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)
# 1. ФУНКЦИЯ ДЛЯ КНОПКИ "МИНУС"
def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete() # Если был 1, то удаляем совсем
        
    return redirect('cart')

# 2. ФУНКЦИЯ ДЛЯ КНОПКИ "МУСОРКА" (Удалить сразу всё)
def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    
    cart_item.delete()
    return redirect('cart')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        cart_items = []

    if request.method == 'POST':
        # 👇 ИСПРАВЛЕНИЕ ЗДЕСЬ: меняем 'store' на 'home'
        if not cart_items:
            return redirect('home')

        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.note = form.cleaned_data['note']
            data.payment_method = form.cleaned_data['payment_method']
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = data.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

            CartItem.objects.filter(cart=cart).delete()

            if data.payment_method == 'Card':
                return redirect('payment', order_id=data.id)
            else:
                PHONE_NUMBER = "996559411114"
                msg_cash = f"👋 Новый заказ #{data.id}\n👤 {data.first_name}\n📞 {data.phone}\n💰 {total} с.\n💳 Оплата: Наличные\n📍 Адрес: {data.address}"
                whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg_cash)}"
                return redirect(whatsapp_url)

    else:
        form = OrderForm()

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        # 🔥 ЗАЩИТА 1: Если корзины нет, делаем пустой список, а не None
        cart_items = []

    if request.method == 'POST':
        # 🔥 ЗАЩИТА 2: Если товаров нет, отправляем в каталог, чтобы не было ошибки
        if not cart_items:
            return redirect('store')

        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.note = form.cleaned_data['note']
            data.payment_method = form.cleaned_data['payment_method']
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Сохраняем товары
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = data.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

            # Очищаем корзину после заказа
            CartItem.objects.filter(cart=cart).delete()

            # Перенаправляем
            if data.payment_method == 'Card':
                return redirect('payment', order_id=data.id)
            else:
                PHONE_NUMBER = "996559411114"
                msg_cash = f"👋 Новый заказ #{data.id}\n👤 {data.first_name}\n📞 {data.phone}\n💰 {total} с.\n💳 Оплата: Наличные\n📍 Адрес: {data.address}"
                whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg_cash)}"
                return redirect(whatsapp_url)

    else:
        form = OrderForm()

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        # Если корзины нет, создаем пустой список, чтобы не было ошибки NoneType
        cart_items = []

    if request.method == 'POST':
        # 👇 ГЛАВНАЯ ЗАЩИТА: Если товаров нет, не пытаемся их сохранить
        if not cart_items:
            return redirect('store') 

        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.note = form.cleaned_data['note']
            data.payment_method = form.cleaned_data['payment_method']
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Сохраняем товары
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = data.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

            # Очищаем корзину
            CartItem.objects.filter(cart=cart).delete()

            # Логика перенаправления
            if data.payment_method == 'Card':
                return redirect('payment', order_id=data.id)
            else:
                PHONE_NUMBER = "996559411114"
                msg_cash = f"👋 Новый заказ #{data.id}\n👤 {data.first_name}\n📞 {data.phone}\n💰 {total} с.\n💳 Оплата: Наличные\n📍 Адрес: {data.address}"
                whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg_cash)}"
                return redirect(whatsapp_url)

    else:
        form = OrderForm()

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # 1. Создаем заказ
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.note = form.cleaned_data['note']
            
            # 👇 2. ВАЖНО: Запоминаем выбор оплаты
            data.payment_method = form.cleaned_data['payment_method']
            
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Сохраняем товары
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = data.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

            # Очищаем корзину
            CartItem.objects.filter(cart=cart).delete()

            # 👇 3. ЛОГИКА ПЕРЕНАПРАВЛЕНИЯ
            if data.payment_method == 'Card':
                # Если выбрали Карту -> Идем на страницу с QR-кодом
                return redirect('payment', order_id=data.id)
            else:
                # Если Наличные -> Сразу в WhatsApp
                PHONE_NUMBER = "996559411114"
                msg = f"👋 Новый заказ #{data.id}\n👤 {data.first_name}\n💰 {total} с.\n💳 Оплата: Наличные"
                whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg)}"
                return redirect(whatsapp_url)

    else:
        form = OrderForm()

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # 1. СНАЧАЛА СОЗДАЕМ ЗАКАЗ (Обязательно первой строкой!)
            data = Order()
            
            # 2. ПОТОМ ЗАПОЛНЯЕМ ДАННЫМИ ИЗ ФОРМЫ
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.note = form.cleaned_data['note']
            data.payment_method = form.cleaned_data['payment_method'] # <--- Выбор оплаты
            
            # 3. ДОБАВЛЯЕМ ТЕХНИЧЕСКИЕ ДАННЫЕ
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            
            # 4. СОХРАНЯЕМ В БАЗУ
            data.save()

            # Сохраняем товары
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = data.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

            # ГЕНЕРИРУЕМ СООБЩЕНИЕ WHATSAPP
            PHONE_NUMBER = "996559411114" 
            
            msg = f"👋 Здравствуйте! Новый заказ #{data.id}\n"
            msg += f"👤 *{data.first_name} {data.last_name}*\n"
            msg += f"📞 {data.phone}\n"
            
            pay_type = "💵 Наличные" if data.payment_method == 'Cash' else "💳 Онлайн / Карта"
            msg += f"💳 Оплата: *{pay_type}*\n"
            
            msg += f"📍 Адрес: {data.city}, {data.address}\n"
            if data.note:
                msg += f"📝 Прим.: {data.note}\n"
            
            msg += "\n🛒 *ЗАКАЗ:*\n"
            for item in cart_items:
                msg += f"— {item.product.name} (x{item.quantity}) = {item.sub_total()} сом\n"
            
            msg += f"\n💰 *ИТОГО: {total} сом*"

            # Очищаем корзину
            CartItem.objects.filter(cart=cart).delete()

            # Отправляем
            whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg)}"
            return redirect(whatsapp_url)

    else:
        form = OrderForm()

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)
    # 1. Считаем корзину
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # ... (сохранение имени, телефона и т.д.) ...
            data.note = form.cleaned_data['note']
            
            # 👇 СОХРАНЯЕМ ВЫБОР ОПЛАТЫ
            data.payment_method = form.cleaned_data['payment_method']
            
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # ... (сохранение товаров в базу OrderProduct - этот кусок кода остается тем же) ...

            # 👇 ГЕНЕРИРУЕМ СООБЩЕНИЕ WHATSAPP С УЧЕТОМ ОПЛАТЫ
            PHONE_NUMBER = "996559411114" 
            
            msg = f"👋 Здравствуйте! Новый заказ #{data.id}\n"
            msg += f"👤 *{data.first_name} {data.last_name}*\n"
            msg += f"📞 {data.phone}\n"
            
            # Добавляем инфо об оплате (переводим на русский для красоты)
            pay_type = "💵 Наличные" if data.payment_method == 'Cash' else "💳 Онлайн / Карта"
            msg += f"💳 Оплата: *{pay_type}*\n"  # <--- ВОТ ТУТ
            
            msg += f"📍 Адрес: {data.city}, {data.address}\n"
            # ... (дальше перечисление товаров и суммы) ...
            if data.note:
                msg += f"📝 Прим.: {data.note}\n"
            
            msg += "\n🛒 *ЗАКАЗ:*\n"
            for item in cart_items:
                msg += f"— {item.product.name} (x{item.quantity}) = {item.sub_total()} c.\n"
            
            msg += f"\n💰 *ИТОГО: {total} сом*"

            # Очищаем корзину
            CartItem.objects.filter(cart=cart).delete()

            # 4. ОТПРАВЛЯЕМ В ВАТСАП
            # Кодируем текст для ссылки (превращаем пробелы в %20 и т.д.)
            whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg)}"
            
            # ... (код выше: сохранение order_product, очистка корзины) ...

            # 👇 ЛОГИКА: Куда отправлять?
            if data.payment_method == 'Card':
                # Если Онлайн -> На страницу с QR-кодом
                return redirect('payment', order_id=data.id)
            else:
                # Если Наличные -> Сразу в WhatsApp (как раньше)
                msg_cash = f"👋 Новый заказ #{data.id}\n👤 {data.first_name}\n💰 {total} с.\n💳 Оплата: Наличные"
                whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg_cash)}"
                return redirect(whatsapp_url)

    else:
        form = OrderForm()

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # 1. Сохраняем сам Заказ
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.note = form.cleaned_data['note']
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save() # Тут создается ID заказа

            # 2. Переносим товары из Корзины в Заказ
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = data.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

            # 3. Очищаем корзину
            CartItem.objects.filter(cart=cart).delete()

            # 4. Идем на страницу успеха
            return render(request, 'store/success.html', {'order': data})
    else:
        form = OrderForm()

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)
def about(request):
    return render(request, 'store/about.html')
def payment(request, order_id):
    # Получаем заказ по номеру
    order = get_object_or_404(Order, id=order_id)
    
    PHONE_NUMBER = "996559411114"
    
    # 👇 ГЕНЕРИРУЕМ СООБЩЕНИЕ ДЛЯ WHATSAPP
    msg = f"⚠️ ПРОВЕРКА ОПЛАТЫ (Заказ #{order.id})\n"
    msg += f"👤 Клиент: {order.first_name} {order.last_name}\n"
    msg += f"💰 Сумма: *{order.total} сом*\n"
    msg += f"💳 Оплата: O!Business / QR / Счет\n\n"
    msg += f"❗ Клиент подтвердил оплату.\n"
    msg += f"Пожалуйста, зайдите в приложение O!Business и проверьте поступление средств."
    
    # Создаем ссылку
    whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg)}"

    context = {
        'order': order,
        'whatsapp_url': whatsapp_url,
    }
    return render(request, 'store/payment.html', context)
    order = get_object_or_404(Order, id=order_id)
    
    PHONE_NUMBER = "996559411114"
    
    # 👇 ТЕКСТ ДЛЯ ТЕТИ (С предупреждением "ПРОВЕРЬ")
    msg = f"⚠️ ПРОВЕРКА ОПЛАТЫ (Заказ #{order.id})\n"
    msg += f"👤 Клиент: {order.first_name} {order.last_name}\n"
    msg += f"💰 Сумма: *{order.total} сом*\n"
    msg += f"💳 Оплата: MBank / Онлайн\n\n"
    msg += f"❗ Клиент сообщил об оплате.\n"
    msg += f"Пожалуйста, зайдите в MBank и проверьте, пришли ли деньги."
    
    whatsapp_url = f"https://wa.me/{PHONE_NUMBER}?text={quote(msg)}"

    context = {
        'order': order,
        'whatsapp_url': whatsapp_url,
    }
    return render(request, 'store/payment.html', context)