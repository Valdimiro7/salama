from django.db import models
from .expensecategory import ExpenseCategory

class Expense(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    expense_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "sl_expenses"

    def __str__(self):
        return f"{self.expense_date} · {self.description} ({self.amount})"