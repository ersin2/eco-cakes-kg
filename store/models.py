from django.db import models

# --- 1. КАТЕГОРИИ И ТОВАРЫ ---

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название категории")
    slug = models.SlugField(unique=True, verbose_name="URL метка")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name="Название торта")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, verbose_name="Описание вкуса")
    
    # Специфика ПП (КБЖУ)
    ingredients = models.TextField(verbose_name="Состав", blank=True)
    calories = models.PositiveIntegerField(verbose_name="Ккал (на 100г)", default=0)
    proteins = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Белки (г)", default=0.0)
    fats = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Жиры (г)", default=0.0)
    carbs = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Углеводы (г)", default=0.0)
    
    # Фильтры
    is_sugar_free = models.BooleanField(default=True, verbose_name="Без сахара")
    is_gluten_free = models.BooleanField(default=False, verbose_name="Без глютена")
    is_vegan = models.BooleanField(default=False, verbose_name="Веган")
    
    # Цена и фото
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена (RM)")
    image = models.ImageField(upload_to='products/', blank=True, verbose_name="Фото")
    is_available = models.BooleanField(default=True, verbose_name="В наличии")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ПП Десерт"
        verbose_name_plural = "ПП Десерты"

    def __str__(self):
        return self.name

# --- 2. КОРЗИНА (ИСПРАВЛЕННАЯ) ---

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'Cart'
        ordering = ['date_added']

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    # ЗДЕСЬ БОЛЬШЕ НЕТ ЛИШНИХ ПОЛЕЙ (Цены или Заказа) - ТЕПЕРЬ ВСЁ ЧИСТО

    class Meta:
        db_table = 'CartItem'
    
    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return str(self.product)

# --- 3. ЗАКАЗЫ (CHECKOUT) ---

class Order(models.Model):
    STATUS = (
        ('New', 'Новый'),
        ('Accepted', 'Принят'),
        ('Completed', 'Выполнен'),
        ('Cancelled', 'Отменен'),
    )

    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    phone = models.CharField(max_length=50, verbose_name="Телефон")
    email = models.EmailField(max_length=50, verbose_name="Email")
    address = models.CharField(max_length=250, verbose_name="Адрес доставки")
    city = models.CharField(max_length=50, verbose_name="Город")
    note = models.TextField(blank=True, verbose_name="Примечание")
    
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    PAYMENT_CHOICES = (
        ('Cash', 'Наличные'),
        ('Card', 'Онлайн / Карта'),
    )
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='Cash')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ {self.id} от {self.first_name}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name
    # Эта таблица связывает Заказ с Товарами
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2) # Фиксируем цену на момент покупки!
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name        