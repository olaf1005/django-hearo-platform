import datetime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import loader

from accounts.models import Profile
from mail.models import Message

from utils import render_appropriately, JSON


@login_required
def index(request):
    template = loader.get_template("mail/index.html")
    to_id = request.GET.get("id")
    if to_id:
        to_profile = Profile.objects.get(id=to_id)
    else:
        to_profile = None
    # m = Message.objects.filter(
    # to_profile=request.user.person.view).order_by('-timestamp')
    return render_appropriately(
        request, template, {"to_profile": to_profile, "user": request.user}
    )


@login_required
def inbox(request):
    template = loader.get_template("mail/inbox.html")
    prof = request.user.person.view
    msg = Message.objects.filter(to_profile=prof, to_deleted=False).order_by(
        "-timestamp"
    )
    sent = Message.objects.filter(from_profile=prof, from_deleted=False).order_by(
        "-timestamp"
    )

    return render_appropriately(
        request, template, {"inbox": msg, "sentbox": sent, "user": request.user}
    )


@login_required
def send_message(request):
    prof = request.user.person.view
    subject = request.POST["subject"]
    message = request.POST["message"]
    send_to = Profile.objects.get(keyword=request.POST["keyword"])
    msg = Message(to_profile=send_to, from_profile=prof, body=message, subject=subject)
    msg.save()
    return render_to_response(
        "common/to_fanmail_message.html",
        {
            "message": msg,
            "timestamp": msg.timestamp.strftime(
                "%B %d %Y at %I:%M %p"
                if msg.timestamp.year != datetime.datetime.now().year
                else "%B %d at %I:%M %p"
            ),
        },
    )


def delete(request):
    message_id = request.POST["id"]
    prof = request.user.person.view
    try:
        # you should only be able to delete messages you receive
        msg = Message.objects.get(id=message_id, to_profile=prof)
        msg.to_deleted = True
        msg.save()
        return HttpResponse()
    except:
        return HttpResponse("failed to delete: no such " "message or not your message")


@login_required
def view(request):
    "View the message"
    prof = request.user.person.view
    template = loader.get_template("mail/view.html")
    messageid = request.GET["messageid"]
    msg = Message.objects.get(id=messageid, to_profile=prof)
    msg.read = True
    msg.save()
    return render_appropriately(request, template, {"message": msg})


@login_required
def mark_read(request):
    prof = request.user.person.view
    message_id = request.POST.get("id")
    # make sure you cant mark a message read of another profile
    msg = Message.objects.get(id=message_id, to_profile=prof)
    msg.read = True
    msg.save()
    return HttpResponse()


@login_required
def check_for_new(request):
    prof = request.user.person.view
    newest_id = request.GET.get("id")
    newer = Message.objects.filter(to_profile=prof, id__gt=newest_id)
    if newer:
        return JSON([m.jsonify(request) for m in newer])
    else:
        return JSON([])


def update_unread(request):
    if request.user.is_authenticated:
        prof = request.user.person.view
        if "on_mail_page" in request.GET:
            messages = prof.get_unread()
            if request.GET["on_mail_page"] == "t":
                prev = int(request.GET["now_count"])
                new = messages[prev : messages.count()]
                html = "".join(
                    [
                        loader.render_to_string(
                            "common/fanmail_message.html",
                            {
                                "message": message,
                                "timestamp": message.timestamp.strftime(
                                    "%B %d %Y at %I:%M %p"
                                    if message.timestamp.year
                                    != datetime.datetime.now().year
                                    else "%B %d at %I:%M %p"
                                ),
                            },
                        )
                        for message in new
                    ]
                )
            else:
                html = ""
            return {"html": html, "count": messages.count()}
    return JSON([])
