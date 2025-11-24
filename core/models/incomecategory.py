from django.db import models
from .companyaccount import CompanyAccount

class IncomeCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "sl_income_categories"

    def __str__(self):
        return self.name



