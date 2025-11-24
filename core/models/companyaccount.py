from django.db import models
from .member import Member
from .accounttype import AccountType

class CompanyAccount(models.Model):
    id = models.BigAutoField(primary_key=True)
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name="company_accounts",
    )
    name = models.CharField(
        max_length=150
    )  # Nome/descrição da conta (ex: “Conta BCI MZN - Salama”)
    account_identifier = models.CharField(
        max_length=100
    )  # número da conta / celular / NIB
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "sl_company_accounts"
