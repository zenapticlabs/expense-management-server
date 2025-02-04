from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', related_name='created_%(class)s_set', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey('users.User', related_name='updated_%(class)s_set', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True

class UppercaseCharField(models.CharField):
    def get_prep_value(self, value):
        return value.upper() if isinstance(value, str) else value

    def from_db_value(self, value, expression, connection):
        return value.upper() if isinstance(value, str) else value
