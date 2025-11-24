from django.db import models
from .loan import Loan

class LoanGuarantee(models.Model):
    id = models.BigAutoField(primary_key=True)
    loan = models.ForeignKey(
        Loan,
        on_delete=models.PROTECT,
        related_name="guarantees",
    )
    name = models.CharField(max_length=150)
    guarantee_type = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    estimated_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    attachment = models.FileField(upload_to="loan_guarantees/%Y/%m/", null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "sl_loan_guarantees"

    def __str__(self):
        return f"{self.name} · {self.loan_id}"
