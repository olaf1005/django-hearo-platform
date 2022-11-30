from notices.models import Notice
from accounts.models import Person


def notice_user(user, notice_string, notice_type):
    """user is expected to be of type Person,
    notice_type is an Integer as specified in notices.models"""

    Notice.objects.create(profile=user, message=notice_string, category=notice_type)


def notice_site(notice_string, notice_type):
    """pushes a notice to all people"""
    for p in Person.objects.all():
        notice_user(p, notice_string, notice_type)


def dismiss_notice(user, notice_id):
    """deletes a notice"""
    Notice.objects.get(id=notice_id, person=user).delete()
