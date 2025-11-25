from django.db import models
from .tuktukleasecontract import TukTukLeaseContract
from .member import Member
from .companyaccount import CompanyAccount


class TukTukLeasePayment(models.Model):
    METHOD_CHOICES = (
        ("cash", "Cash"),
        ("bank_transfer", "Transferência bancária"),
        ("mobile_wallet", "Carteira móvel"),
    )

    id = models.BigAutoField(primary_key=True)
    contract = models.ForeignKey(
        TukTukLeaseContract,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    driver = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="tuktuk_lease_payments",
    )
    company_account = models.ForeignKey(
        CompanyAccount,
        on_delete=models.PROTECT,
        related_name="tuktuk_lease_payments",
    )

    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default="cash",
    )

    attachment = models.FileField(
        upload_to="tuktuk_lease_payments/%Y/%m/",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "sl_tuktuk_lease_payments"

    def __str__(self):
        return f"Pagamento TukTuk #{self.id} · Contrato {self.contract_id}"
