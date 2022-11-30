from django.db import models
from django.contrib.auth.models import User
from accounts.models import Profile
from utils import pretty_money


class CreditCard(models.Model):
    "User credit cards used for purchases"

    # TODO: review inconsistent usage of user vs profile in bankinfo
    # related methods found in my.py
    user = models.ForeignKey(
        User, related_name="credit_cards", on_delete=models.CASCADE
    )
    last4 = models.CharField(max_length=4)
    cardType = models.CharField(max_length=20)  # American Express, Visa, etc.
    stripe_id = models.CharField(max_length=20)


class BankInfo(models.Model):
    "Musician bank info used to cash out"
    profile = models.ForeignKey(Profile, related_name="bank", on_delete=models.CASCADE)
    routing_number = models.CharField(max_length=9)
    account_number = models.CharField(max_length=17)
    account_holder_name = models.CharField(max_length=22)
    verified = models.BooleanField(default=False)


class Receipt(models.Model):
    "Musician cash out receipts"
    time_cashed = models.DateTimeField(auto_now=True)
    profile = models.ForeignKey(
        Profile, related_name="receipts", on_delete=models.CASCADE
    )
    error_message = models.CharField(max_length=40, null=True, blank=True)

    state = models.CharField(
        max_length=255,
        choices=(
            ("unknown", "Status is unknown."),
            ("pending", "Pending transmission to bank."),
            ("error", "There was an error processing this reciept."),
            ("batched", "Sent to the bank successfully!"),
        ),
    )

    def __str__(self):
        return "Receipt for %s - %s downloads - %s profit" % (
            self.profile.name,
            len(self.downloads.all()),
            self.get_total_profit(),
        )

    def record_error(self, error):
        self.error_message = error
        self.status = "error"
        self.save()

    def num_users(self):
        return len(set([x.charge.profile for x in self.downloads.all()]))

    def get_total_price(self):
        total = 0
        for download in self.downloads.all():
            total += download.price
        return pretty_money(total)

    def get_total_hearo_fee(self):
        total = 0
        for download in self.downloads.all():
            total += download.hearo_fee()
        return pretty_money(total)

    def get_total_profit_raw(self):
        return sum([d.profit() for d in self.downloads.all()])

    def get_total_profit(self):
        total = 0
        for download in self.downloads.all():
            total += download.profit()
        return pretty_money(total)

    def get_total_stripe_fee(self):
        total = 0
        for download in self.downloads.all():
            total += download.stripe_fee()
        return pretty_money(total)

    def num_downloads(self):
        return len(self.downloads.all())
