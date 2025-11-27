from django.db import models
from django.conf import settings

from .leasedvehicle import LeasedVehicle
from .member import Member
from .companyaccount import CompanyAccount


class VehicleLeaseContract(models.Model):
    STATUS_CHOICES = (
        ("active", "Activo"),
        ("finished", "Terminado"),
        ("cancelled", "Cancelado"),
    )

    id = models.BigAutoField(primary_key=True)

    leased_vehicle = models.ForeignKey(
        LeasedVehicle,
        on_delete=models.PROTECT,
        related_name="lease_contracts",
        verbose_name="Viatura em leasing",
    )

    driver = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="vehicle_lease_contracts",
        help_text="Motorista / cliente responsável pelos pagamentos semanais.",
    )

    company_account = models.ForeignKey(
        CompanyAccount,
        on_delete=models.PROTECT,
        related_name="vehicle_lease_contracts",
        help_text="Conta da empresa que recebe as prestações.",
    )

    start_date = models.DateField("Data de início")
    end_date = models.DateField("Data prevista fim", blank=True, null=True)

    weekly_rent = models.DecimalField(
        "Valor semanal (MT)", max_digits=15, decimal_places=2
    )

    payment_weekday = models.PositiveSmallIntegerField(
        "Dia da semana para pagamento",
        blank=True,
        null=True,
        help_text="1 = Segunda, 7 = Domingo (opcional, só para controlo).",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_vehicle_lease_contracts",
        blank=True,
        null=True,
    )

    notes = models.TextField("Notas", blank=True, null=True)

    class Meta:
        managed = False
        # Mantemos a mesma tabela antiga, para não partir a BD
        db_table = "sl_vehicle_lease_contracts"

    def __str__(self):
        return f"Contrato #{self.id} · {self.leased_vehicle} · {self.driver}"
