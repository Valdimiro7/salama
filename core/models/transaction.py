from django.db import models
from .companyaccount import CompanyAccount


class Transaction(models.Model):
    TX_TYPE_IN = "IN"
    TX_TYPE_OUT = "OUT"
    TX_TYPE_CHOICES = (
        (TX_TYPE_IN, "Entrada"),
        (TX_TYPE_OUT, "Saída"),
    )

    id = models.BigAutoField(primary_key=True)
    company_account = models.ForeignKey(
        CompanyAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    tx_type = models.CharField(max_length=3, choices=TX_TYPE_CHOICES)
    source_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Origem: income, expense, manual, etc.",
    )
    source_id = models.BigIntegerField(blank=True, null=True)
    tx_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "sl_transactions"

    def __str__(self):
        return f"{self.tx_date} · {self.company_account.name} · {self.tx_type} {self.amount}"
