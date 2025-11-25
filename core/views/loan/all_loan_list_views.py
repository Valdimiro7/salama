# core/views/loans/loan_list_views.py
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import Loan  # ajusta o import conforme o teu projecto


@login_required
def loan_list_all(request):
    """
    Lista TODOS os empréstimos (independentemente do status)
    + KPIs da carteira.
    """
    loans_qs = (
        Loan.objects
        .select_related("member", "loan_type", "interest_type", "approved_by", "company_account")
        .prefetch_related("disbursements")
        .order_by("-created_at")
    )

    loans = list(loans_qs)

    total_loans = len(loans)
    total_principal = Decimal("0")
    total_to_repay = Decimal("0")
    total_interest = Decimal("0")

    status_counts = {
        "pending": 0,
        "approved": 0,
        "disbursed": 0,
        "closed": 0,
        "cancelled": 0,
    }

    for loan in loans:
        principal = loan.principal_amount or Decimal("0")
        rate = getattr(loan.interest_type, "rate", Decimal("0")) or Decimal("0")
        periods = loan.term_periods or 1

        # Juros simples “flat”: principal * (taxa% * períodos)
        interest = (principal * rate * periods) / Decimal("100")
        total_amount = principal + interest

        loan.total_interest = interest
        loan.total_to_repay = total_amount

        # Último desembolso (se existir)
        last_disb = (
            loan.disbursements.order_by("-disburse_date", "-id").first()
            if hasattr(loan, "disbursements")
            else None
        )
        loan.disbursed_date = last_disb.disburse_date if last_disb else None
        loan.disbursed_amount = last_disb.amount if last_disb else None
        loan.disbursed_company_account = last_disb.company_account if last_disb else None

        total_principal += principal
        total_interest += interest
        total_to_repay += total_amount

        if loan.status in status_counts:
            status_counts[loan.status] += 1

    context = {
        "loans": loans,
        "kpi_total_loans": total_loans,
        "kpi_total_principal": total_principal,
        "kpi_total_interest": total_interest,
        "kpi_total_to_repay": total_to_repay,
        "kpi_status_pending": status_counts["pending"],
        "kpi_status_approved": status_counts["approved"],
        "kpi_status_disbursed": status_counts["disbursed"],
        "kpi_status_closed": status_counts["closed"],
        "kpi_status_cancelled": status_counts["cancelled"],
    }
    return render(request, "loan/loan_list_all.html", context)
