from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View

import os
from . import models


def website_home(request):
    if request.user.is_authenticated:
        return redirect('appboard:home')

    template_name = 'website/home.html'
    context = {}
    return render(request, template_name, context=context)


def contact_message(request):
    if request.method == "POST":
        data = request.POST
        models.ContactMessage.objects.create(
            name=data['name'],
            email=data['email'],
            subject=data['subject'],
            body=data['body']
        )
        messages.success(request, 'Your message has been sent! Thank You')
        return redirect('website:home')

    messages.error(request, 'Something wrong happened!')
    return redirect('website:home')
