from django.contrib import admin
from django.utils.html import mark_safe
from .models import Product, Category, Order, OrderProduct

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('product', 'quantity', 'product_price')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'phone', 'payment_method', 'total', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    list_editable = ['status']
    inlines = [OrderProductInline]

class ProductAdmin(admin.ModelAdmin):
    list_display = ('get_image', 'name', 'price', 'category', 'is_available')
    list_editable = ('price', 'is_available')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" style="border-radius:5px;">')
        return "-"
    get_image.short_description = "Фото"

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug')

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Order, OrderAdmin)