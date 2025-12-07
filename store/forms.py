from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        # 👇 ПРОВЕРЬ ЭТУ СТРОКУ! Слово 'payment_method' ОБЯЗАНО быть тут
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'city', 'note', 'payment_method']
        widgets = {
             # Это делает кнопки выбора вместо обычного списка
            'payment_method': forms.RadioSelect(),
        }