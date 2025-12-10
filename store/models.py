from django.db import models
from django.urls import reverse

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.category_name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=200, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=500, blank=True, verbose_name="Описание")
    price = models.IntegerField(verbose_name="Цена")
    image = models.ImageField(upload_to='photos/products', verbose_name="Фото")
    is_available = models.BooleanField(default=True, verbose_name="В наличии")
    
    # КБЖУ
    ingredients = models.TextField(blank=True, verbose_name="Состав")
    calories = models.IntegerField(null=True, blank=True, verbose_name="Ккал")
    protein = models.FloatField(null=True, blank=True, verbose_name="Белки")
    fat = models.FloatField(null=True, blank=True, verbose_name="Жиры")
    carbs = models.FloatField(null=True, blank=True, verbose_name="Углеводы")
    
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.name

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return str(self.product)

class Order(models.Model):
    STATUS_CHOICES = (
        ('New', 'Новый'),
        ('Accepted', 'Принят'),
        ('Completed', 'Выполнен'),
        ('Cancelled', 'Отменен'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Наличными'),
        ('card', 'QR / Перевод'),
    )

    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, blank=True, verbose_name="Фамилия")
    phone = models.CharField(max_length=50, verbose_name="Телефон")
    address = models.CharField(max_length=250, verbose_name="Адрес")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name="Оплата")
    
    total = models.FloatField(default=0, verbose_name="Сумма")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New', verbose_name="Статус")
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ {self.id} ({self.first_name})'

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.name