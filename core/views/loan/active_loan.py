# core/views/payments/loan_disbursement_views.py  (ou outro módulo de loans)

from decimal import Decimal
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import F, ExpressionWrapper, DecimalField
from django.shortcuts import render
from django.utils import timezone

from core.models import Loan, LoanDisbursement, CompanyAccount, ClientAccount


#============================================================================================================
#============================================================================================================

@login_required
def active_loans_list(request):
    """
    Lista de empréstimos activos (status='disbursed'):
    - Mostra info básica do empréstimo
    - Juros e total a reembolsar
    - Conta da empresa por onde saiu o dinheiro
    - Quem requisitou/aprovou
    """

    loans_qs = (
        Loan.objects
        .select_related("member", "loan_type", "approved_by")
        .prefetch_related(
            "disbursements",
            "disbursements__company_account",
        )
        .filter(status="disbursed")
        .annotate(
            total_to_repay=ExpressionWrapper(
                F("payment_per_period") * F("term_periods"),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
            total_interest=ExpressionWrapper(
                F("payment_per_period") * F("term_periods") - F("principal_amount"),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        )
        .order_by("-id")
    )

    # Transformar em lista para anexar info calculada
    loans = list(loans_qs)

    for loan in loans:
        # último desembolso (normalmente só 1, mas deixamos genérico)
        last_disb = loan.disbursements.order_by("-disburse_date", "-id").first()
        loan.last_disbursement = last_disb

        if last_disb:
            loan.disbursed_amount = last_disb.amount
            loan.disbursed_date = last_disb.disburse_date
            loan.disbursed_company_account = last_disb.company_account
        else:
            loan.disbursed_amount = None
            loan.disbursed_date = None
            loan.disbursed_company_account = None

    context = {
        "loans": loans,
    }
    return render(request, "loan/active_loans_list.html", context)


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================