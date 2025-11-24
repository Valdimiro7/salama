from django.db import models
from .incomecategory import IncomeCategory
from .companyaccount import CompanyAccount

class Income(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        IncomeCategory,
        on_delete=models.PROTECT,
        related_name="incomes",
    )
    company_account = models.ForeignKey(
        CompanyAccount,
        on_delete=models.PROTECT,
        related_name="incomes",
    )
    income_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    attachment = models.FileField(                
        max_length=255,
        upload_to="incomes/%Y/%m/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "sl_incomes"

    def __str__(self):
        return f"{self.income_date} · {self.description} ({self.amount})"
