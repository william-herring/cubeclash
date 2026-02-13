from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponseForbidden, HttpResponseServerError, JsonResponse
from .tasks import join_battle_queue
from .models import Battle


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

class MatchmakingView(TemplateView):
    template_name = 'matchmaking.html'

    def get_context_data(self, **kwargs):
        context = super(MatchmakingView, self).get_context_data(**kwargs)
        context['matchmaking_socket_id'] = self.request.GET.get('socket_id')

        return context

class JoinBattleView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        if request.GET.get('opponent_type') == 'random':
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

        else:
            battle = Battle(
                battle_type=request.GET.get('battle_type'),
                user1=request.user,
            )
            battle.save()

            return JsonResponse({
                'message': 'Created battle',
                'battle': {
                    'id': battle.pk,
                }
            }, status=201)