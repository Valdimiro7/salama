from django.db import models
from .member import Member
from .accounttype import AccountType

class ClientAccount(models.Model):
    id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="client_accounts",
    )
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name="client_accounts",
    )
    account_identifier = models.CharField(
        max_length=100
    )  # número de conta / celular / NIB
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "sl_client_accounts"


