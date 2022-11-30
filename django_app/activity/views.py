from django.template import loader
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from accounts.models import Profile
from activity.models import Feed

from utils import JSON


@login_required
def get(request):
    user = request.user

    slug = request.GET.get("keyword")
    page = int(request.GET.get("page", 1))
    page_size = 25

    if slug:
        try:
            profile_get = Profile.objects.get(keyword=slug)
        except Profile.DoesNotExist:
            return HttpResponseRedirect("/")
    else:
        profile_get = user.profile

    total = Feed.count_user_feed_for(profile_get)
    feeds = Feed.decorated_user_feed_for(profile_get, request, False, page, page_size)
    # t = loader.get_template('activity/updates.html')
    html = loader.render_to_string("activity/updates.html", {"feeds": feeds})
    last = page * page_size

    data = {"more": last < total, "count": len(feeds), "html": html}

    return JSON(data)
