from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('cart/', views.cart, name='cart'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    
    # Кнопка "Минус" (уменьшить количество)
    path('remove_cart/<int:product_id>/', views.remove_cart, name='remove_cart'),
    
    # ВОТ ЭТОЙ СТРОЧКИ НЕ ХВАТАЛО 👇 (Кнопка "Мусорка")
    path('remove_cart_item/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),
    
    path('checkout/', views.checkout, name='checkout'),
]