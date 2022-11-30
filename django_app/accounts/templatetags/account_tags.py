"""
Inclusion tags for common elements used in most templates.
To use in a new template, prepend tag {% load elements %}
"""
import logging

from django.template import Library

from accounts.models import User, Wallet, HTSTokenTransfer


register = Library()
logger = logging.getLogger(__name__)


@register.filter
def org_user_is_admin_or_profile_owner(org, view):
    return org.user_is_admin_or_profile_owner(view)


@register.inclusion_tag("common/repeater.html")
def num_users():
    return {"value": User.objects.count()}


@register.inclusion_tag("common/repeater.html")
def num_users_with_wallets():
    return {"value": Wallet.objects.count()}


@register.inclusion_tag("common/repeater.html")
def num_transactions():
    return {"value": HTSTokenTransfer.objects.count()}
