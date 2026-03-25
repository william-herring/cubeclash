from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponseForbidden, HttpResponseServerError, JsonResponse
from .tasks import join_battle_queue
from .models import Battle
from .utils import init_sets


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

class BattleView(LoginRequiredMixin, DetailView):
    model = Battle
    template_name = 'battle_detail.html'

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

class CreateBattleView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        battle = Battle(
            battle_type=request.POST.get('battle_type'),
            competitor_1_id=request.user.pk,
        )
        battle.save()

        for set_obj in init_sets(battle):
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

        if join_result.get('status') == 'joined':
            return JsonResponse({
                'message': 'Joined queue',
                'position_id': join_result.get('position_id'),
            }, status=200)
        else:
            return HttpResponseServerError()
