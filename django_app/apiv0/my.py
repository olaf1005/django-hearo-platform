from apiv0.decorator import api_v0
from utils import JSON

from accounts.models import Person


@api_v0
def cards(request, profile):
    if not profile:
        return JSON([])

    # If the profile has an associated user, make sure the current user is an
    # admin of the account to allow them to use the credit card
    if profile.user and profile.organization.user_is_admin_or_profile_owner(
        request.user.profile
    ):
        # credit_cards = request.user.credit_cards.all() # Alternatively, we could use own cards?
        credit_cards = profile.user.credit_cards.all()
    else:
        return JSON([])

    return JSON(
        [
            {"last4": card.last4, "type": card.cardType, "stripe_id": card.stripe_id}
            for card in credit_cards
        ]
    )
