from django.db import models
from django.conf import settings

from .expensecategory import ExpenseCategory
from .companyaccount import CompanyAccount


class Expense(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    company_account = models.ForeignKey(
        CompanyAccount,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    expense_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    attachment = models.FileField(
        max_length=255,
        upload_to="expenses/%Y/%m/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expenses_created",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "sl_expenses"

    def __str__(self):
        return f"{self.expense_date} · {self.description} · {self.amount}"
