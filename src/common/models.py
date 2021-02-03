from django.db import models


class ExchangeReadUsingDBMixin:
    def get_using(self):
        return 'exchange_read'


class ExchangeReadManager(ExchangeReadUsingDBMixin, models.Manager):
    def get_queryset(self):
        return models.QuerySet(self.model, using=self.get_using())


class ExchangeDefaultManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(self.model, using='default')
