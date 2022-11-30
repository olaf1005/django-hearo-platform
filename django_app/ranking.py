from datetime import date, timedelta


def update(self):
    "Helper for save method in models which expose rank fields"
    today = date.today()
    self.rank_all = self.hottness(None)
    self.rank_today = self.hottness(today - timedelta(1))
    self.rank_week = self.hottness(today - timedelta(7))
    self.rank_month = self.hottness(today - timedelta(31))
    self.rank_year = self.hottness(today - timedelta(365))
    self.save()
