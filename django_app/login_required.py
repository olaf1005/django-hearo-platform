import socket
import logging

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings

from django_user_agents.utils import get_user_agent
from ipware import get_client_ip


logger = logging.getLogger(__name__)


def is_google_bot(request):
    user_agent = get_user_agent(request)
    if not user_agent.is_bot:
        return False
    ip, _ = get_client_ip(request)
    try:
        host = socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.error):
        return False
    domain_name = ".".join(host.split(".")[1:])
    if domain_name not in ["googlebot.com", "google.com"]:
        return False
    host_ip = socket.gethostbyname(host)
    return host_ip == ip


class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings by setting a tuple of routes to ignore
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        The Login Required middleware needs to be after AuthenticationMiddleware.
        Also make sure to include the template context_processor:
        'django.contrib.auth.context_processors.auth'.
        """

        if request.user.is_anonymous:
            logging.debug(request.path)
            route_exempt = any(
                [route.match(request.path[1:]) for route in settings.AUTH_EXEMPT_ROUTES]
            )
            if route_exempt or is_google_bot(request):
                return self.get_response(request)
            return HttpResponseRedirect(
                "{}?next={}".format(settings.AUTH_LOGIN_ROUTE, request.path)
            )
        else:
            if settings.REQUIRE_VERIFICATION_FOR_LOGIN:
                if not request.user.person.verified:
                    return HttpResponseRedirect(reverse("not_verified"))
            return self.get_response(request)
