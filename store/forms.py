from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'city', 'note', 'payment_method'] # <--- Добавили payment_method
        widgets = {
            'payment_method': forms.RadioSelect(), # Делаем кружочки для выбора
        }