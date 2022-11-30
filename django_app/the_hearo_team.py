from accounts.models import Profile
from mail.models import Message
from django.conf import settings

message = "Thanks for joining the ultimate music social network {}! It's the \
best place to connect directly with musicians and fans. Here in Fanmail, \
you can messages musicians and fans you like or want to play music with. \
Have fun!".format(
    settings.BASE_URL
)

subject = "Welcome to {}!".format(settings.BASE_URL)


def send_intro(prof):
    if settings.HEARO_TEAM_PROFILE_ID:
        team = Profile.objects.get(id=settings.HEARO_TEAM_PROFILE_ID)
        Message.objects.create(
            to_profile=prof, from_profile=team, body=message, subject=subject
        )


def send_msg(prof, subject, body):
    if settings.HEARO_TEAM_PROFILE_ID:
        team = Profile.objects.get(id=settings.HEARO_TEAM_PROFILE_ID)
        Message.objects.create(
            to_profile=prof, from_profile=team, body=body, subject=subject
        )
