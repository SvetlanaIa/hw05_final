from django.shortcuts import render, redirect
# позволяет узнать ссылку на URL по его имени, параметр name функции path
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm
from django.core.mail import send_mail


class SignUp(CreateView):
    form_class = CreationForm
    success_url = "/auth/login/"
    template_name = "signup.html"

    send_mail(
        'Тема письма',
        'Текст письма.',
        'from@example.com',  # Это поле От:
        ['to@example.com'],  # Это поле Кому:
        fail_silently=False,  # сообщать об ошибках
    )
