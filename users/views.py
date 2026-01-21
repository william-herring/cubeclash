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

        user_response = requests.get('https://www.worldcubeassociation.org/api/v0/me', headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        })

        data = user_response.json()['me']
        print(data)

        # Unfortunate workaround as cannot catch the DoesNotExist exception
        users_result = User.objects.filter(email=data['email']).all()
        if len(users_result) > 0:
            login(request, users_result[0])
        else:
            name_parts = data['name'].split(None, 1)
            user = User(
                email=data['email'],
                first_name=name_parts[0],
                last_name=name_parts[1],
                avatar=data['avatar']['thumb_url']
            )
            user.set_unusable_password()

            if 'wca_id' in data:
                user.wca_id = data['wca_id']
                user.username = data['wca_id']
            else:
                user.username = generate_username(1)[0]

            user.save()

            login(request, user)
            return redirect('/profile')

        return redirect('/battle')