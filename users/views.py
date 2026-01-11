from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.views import View


class LoginView(View):
    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'form': form, 'invalid_details': True})

    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})
