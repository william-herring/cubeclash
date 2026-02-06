from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseForbidden
from .tasks import join_battle_queue
from .models import Battle


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

class MatchmakingView(TemplateView):
    template_name = 'matchmaking.html'

    def get_context_data(self, **kwargs):
        context = super(MatchmakingView, self).get_context_data(**kwargs)
        context['matchmaking_socket_id'] = self.request.GET.get('socket_id')

        return context

class JoinBattleView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        if request.POST.get('matchmaking'):
            join_battle_queue.delay(
                request.user.pk,
                request.user.elo,
                request.POST.get('battle_type')
            )

        else:
            battle = Battle(
                battle_type=request.POST.get('battle_type'),
                user1=request.user,
            )
            battle.save()

            return HttpResponse(battle.pk, status=201)