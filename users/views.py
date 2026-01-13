import os
import requests
from random_username.generate import generate_username
from django.contrib.auth import login
from django.shortcuts import redirect
from dotenv import load_dotenv
from django.views import View
from django.views.generic import TemplateView
from .models import User


class LoginView(TemplateView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('/battle')
        return super().get(request, *args, **kwargs)

class AuthRedirectView(View):
    def get(self, request, *args, **kwargs):
        load_dotenv()

        code = request.GET.get('code')

        token_response = requests.post(
            'https://www.worldcubeassociation.org/oauth/token',
            headers={'Content-Type': 'application/json'},
            params={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': os.getenv('WCA_APP_ID'),
                'client_secret': os.getenv('WCA_APP_SECRET'),
                'redirect_uri': f'{os.getenv('BASE_URL')}/account-redirect'
            }
        )

        if token_response.status_code != 200:
            return redirect('/login')

        token = token_response.json()['access_token']
        print(token)

        user_response = requests.get('https://www.worldcubeassociation.org/api/v0/me', headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        })
        print(user_response.status_code)

        data = user_response.json()['me']
        print(data)

        try:
            login(request, User.objects.get(email=data['email']))
        except User.DoesNotExist:
            name_parts = data['name'].split(None, 1)
            user = User(
                email=data['email'],
                first_name=name_parts[0],
                last_name=name_parts[1],
            )
            user.set_unusable_password()
            if data['wca_id']:
                User.wca_id = data['wca_id']
                User.username = data['wca_id']
            else:
                User.username = generate_username(1)[0]

            login(request, user)
            return redirect('/profile')

        return redirect('/battle')