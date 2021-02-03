from django.contrib.auth.models import User
from django.db import models
from django.utils.functional import cached_property

from constant_core.models import User as CoreUser


class ConstUser(User):
    class Meta:
        managed = False

    user_id = models.IntegerField()
    token = models.TextField()
    company_id = models.IntegerField()  # Current working company

    @staticmethod
    def from_user(user: CoreUser):
        return ConstUser(
            user_id=user.id,
            email=user.email
        )

    @cached_property
    def get_db_user(self) -> CoreUser:
        return CoreUser.objects.get(id=self.user_id)

    @property
    def c_first_name(self):
        return self.get_db_user.first_name

    @property
    def c_middle_name(self):
        return self.get_db_user.middle_name

    @property
    def c_last_name(self):
        return self.get_db_user.last_name

    @property
    def full_name(self) -> str:
        return '%s %s'.format(self.c_first_name, self.c_last_name)

    def build_dict(self) -> dict:
        return {
            'full_name': self.full_name,
            'email': self.email,
        }


class SystemConstUser(ConstUser):
    class Meta:
        managed = False
        proxy = True

    @cached_property
    def get_db_user(self) -> CoreUser:
        return CoreUser.objects.get(id=self.user_id)

    @property
    def c_first_name(self):
        return self.get_db_user.first_name

    @property
    def c_middle_name(self):
        return self.get_db_user.middle_name

    @property
    def c_last_name(self):
        return self.get_db_user.last_name

    @property
    def full_name(self) -> str:
        return '%s %s'.format(self.c_first_name, self.c_last_name)
