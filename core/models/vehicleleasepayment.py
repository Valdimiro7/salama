# core/models/vehicleleasepayment.py

from django.db import models
from django.conf import settings
from .vehicleleasecontract import VehicleLeaseContract
from .member import Member
from .companyaccount import CompanyAccount


class VehicleLeasePayment(models.Model):
    METHOD_CHOICES = (
        ("cash", "Cash"),
        ("bank_transfer", "Transferência bancária"),
        ("mobile_wallet", "Carteira móvel"),
    )

    id = models.BigAutoField(primary_key=True)

    contract = models.ForeignKey(
        VehicleLeaseContract,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Contrato de leasing",
    )

    driver = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="vehicle_lease_payments",
    )

    company_account = models.ForeignKey(
        CompanyAccount,
        on_delete=models.PROTECT,
        related_name="vehicle_lease_payments",
    )

    payment_date = models.DateField("Data de pagamento")
    amount = models.DecimalField("Valor pago (MT)", max_digits=15, decimal_places=2)

    method = models.CharField(
        "Método de pagamento",
        max_length=20,
        choices=METHOD_CHOICES,
        default="cash",
    )

    attachment = models.FileField(
        upload_to="vehicle_lease_payments/%Y/%m/",
        blank=True,
        null=True,
    )

    notes = models.TextField("Notas", blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_lease_payments_created",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "sl_vehicle_lease_payments"

    def __str__(self):
        return f"Pagamento leasing #{self.id} · Contrato {self.contract_id}"
