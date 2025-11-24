from django.db import models
from .loan import Loan
from .member import Member

class LoanGuarantor(models.Model):
    id = models.BigAutoField(primary_key=True)
    loan = models.ForeignKey(
        Loan,
        on_delete=models.PROTECT,
        related_name="loan_guarantors",
    )
    guarantor = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="as_guarantor_in_loans",
    )
    account_number = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "sl_loan_guarantors"

    def __str__(self):
        return f"{self.guarantor} · Loan {self.loan_id}"
