from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        # 👇 Важно: 'payment_method' должен быть в списке!
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'city', 'note', 'payment_method']
        widgets = {
            'payment_method': forms.RadioSelect(),
        }