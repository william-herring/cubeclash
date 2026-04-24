import json
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponseForbidden, HttpResponseServerError, JsonResponse, HttpResponseNotFound

from users.models import User
from .constants import BATTLE_FORMATS
from .tasks import join_battle_queue, leave_battle_queue
from .models import Battle
from .utils import init_set


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        battles = (Battle.objects.filter(Q(competitor_1=self.request.user.pk) | Q(competitor_2=self.request.user.pk))
                   .order_by('-end')[:4]
                   .values('id', 'battle_type', 'competitor_1', 'competitor_2', 'winner', 'was_forfeited', 'end'))
        result = []
        for battle in battles:
            detail = battle
            detail['opponent'] = User.objects.get(id=battle['competitor_2']) if battle['competitor_1'] == self.request.user.pk else User.objects.get(id=battle['competitor_1'])
            detail['battle_type'] = BATTLE_FORMATS[battle['battle_type']]['display']
            if battle['winner'] == self.request.user.pk:
                detail['result'] = 'win'
                result.append(detail)
            elif battle['was_forfeited']:
                detail['result'] = 'forfeit'
                result.append(detail)
            elif battle['winner'] is not None:
                detail['result'] = 'loss'
                result.append(detail)

        context['recent_battles'] = result
        return context

class BattleView(LoginRequiredMixin, DetailView):
    model = Battle
    template_name = 'battle_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.end is not None:
            return redirect(request.path + 'details/')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        waiting_for_opponent = self.object.competitor_2 is None
        competitor_number = 1 if self.object.competitor_1_id == self.request.user.pk else 2

        if waiting_for_opponent and competitor_number == 1:
            context['base_url'] = settings.BASE_URL
        elif competitor_number == 2:
                self.object.competitor_2 = self.request.user
                self.object.save()
                waiting_for_opponent = False

        if not waiting_for_opponent:
            current_set = self.object.sets.all().last()
            current_scramble = current_set.scramble_set.split(';')[-1]
            context['current_scramble'] = current_scramble

        context['waiting_for_opponent'] = waiting_for_opponent
        context['user_competitor_number'] = competitor_number

        return context

class BattleOverviewView(LoginRequiredMixin, DetailView):
    model = Battle
    template_name = 'battle_overview_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['battle_type_display'] = BATTLE_FORMATS[self.object.battle_type]['display']
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.end is None:
            return HttpResponseNotFound()

        return super().get(request, *args, **kwargs)

class CreateBattleView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        battle = Battle(
            battle_type=request.POST.get('battle_type'),
            competitor_1_id=request.user.pk,
        )
        battle.save()

        set_obj = init_set(battle)
        set_obj.battle = battle
        set_obj.save()

        return redirect(f'/battle/b/{battle.pk}/')

class JoinBattleView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        join_result = join_battle_queue.delay(
            request.user.pk,
            request.user.elo,
            request.GET.get('battle_type')
        ).get()

        if join_result.get('status') == 'joined_queue':
            return JsonResponse({
                'message': 'Joined queue',
                'position_id': join_result.get('position_id'),
            }, status=200)
        else:
            return HttpResponseServerError()

class CancelMatchmakingView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        data = json.loads(request.body)

        exit_result = leave_battle_queue.delay(
            request.user.pk,
            request.user.elo,
            data.get('battle_type'),
        ).get()

        print(exit_result)

        if exit_result.get('status') == 'left_queue':
            return JsonResponse({
                'message': 'Left queue',
            }, status=200)
        else:
            return HttpResponseServerError()
