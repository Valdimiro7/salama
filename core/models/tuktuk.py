from django.db import models

class TukTuk(models.Model):
    STATUS_CHOICES = (
        ("available", "Disponível"),
        ("leased", "Em leasing"),
        ("maintenance", "Em manutenção"),
        ("inactive", "Inactivo"),
    )

    id = models.BigAutoField(primary_key=True)
    plate_number = models.CharField("Matrícula", max_length=20, unique=True)
    model = models.CharField("Modelo", max_length=100, blank=True, null=True)
    year = models.PositiveIntegerField("Ano", blank=True, null=True)
    chassis_number = models.CharField("Nº de chassis", max_length=100, blank=True, null=True)

    weekly_rent_default = models.DecimalField(
        "Renda semanal padrão (MT)", max_digits=15, decimal_places=2, default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
    )

    notes = models.TextField("Notas", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "sl_tuktuks"

    def __str__(self):
        return f"{self.plate_number} · {self.model or ''}".strip()
