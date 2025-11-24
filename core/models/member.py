from django.db import models
from django.conf import settings

class Member(models.Model):
    id = models.BigAutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    is_company = models.BooleanField(default=False)
    phone      = models.CharField(max_length=30)
    alt_phone  = models.CharField(max_length=30, blank=True, null=True)
    email      = models.EmailField(blank=True, null=True)
    city       = models.CharField(max_length=100, blank=True, null=True)
    address    = models.CharField(max_length=255, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    gender         = models.CharField(max_length=10, blank=True, null=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='members'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'sl_members'


    def __str__(self):
        base = f"{self.first_name} {self.last_name}".strip()
        if self.is_company and self.legal_name:
            return f"{self.legal_name} ({base})"
        return base
