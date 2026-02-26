from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class RegistrationForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}))
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтвердите пароль'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}))
    company = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Компания'}))
    position = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Должность'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data

    def save(self):
        """Создает нового пользователя"""
        data = self.cleaned_data
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            company=data.get('company', ''),
            position=data.get('position', '')
        )
        return user


class ContactForm(forms.Form):
    city = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}))
    street = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Улица'}))
    house = forms.CharField(required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Дом'}))
    structure = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Корпус'}))
    building = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Строение'}))
    apartment = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Квартира'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}))