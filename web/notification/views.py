from http import HTTPStatus

from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View


# Create your views here.
User = get_user_model()


class IndexView(LoginRequiredMixin, View):
    template = 'notification/index.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template, context)


class RoomView(LoginRequiredMixin, View):
    template = 'notification/rooms.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template, context)


class ToggleView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        email = {
            'admin@email.com': 'user1@email.com',
            'user1@email.com': 'user2@email.com',
            'user2@email.com': 'user3@email.com',
            'user3@email.com': 'admin@email.com',
        }.get(request.user.email)

        user = User.objects.get(email=email)
        login(request, user)

        return redirect('notification:index')
