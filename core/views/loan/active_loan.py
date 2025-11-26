# core/views/payments/loan_disbursement_views.py  (ou outro módulo de loans)

from decimal import Decimal
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from core.models import (
    Loan,
    LoanDisbursement,
    LoanGuarantor,
    LoanGuarantee,
    CompanyAccount,
    ClientAccount,
    Member,
)

#============================================================================================================
#============================================================================================================
@login_required
def active_loans_list(request):
    """
    Lista de empréstimos activos (status='disbursed'):
    - Mostra info base + conta da empresa usada no desembolso
    - Calcula juros e total a reembolsar
    - Gera KPIs para o topo da página
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

    loans = list(loans_qs)

    total_principal = Decimal("0")
    total_to_repay = Decimal("0")
    total_interest_sum = Decimal("0")

    for loan in loans:
        # último desembolso associado
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

        # KPIs
        if loan.principal_amount:
            total_principal += loan.principal_amount
        if getattr(loan, "total_to_repay", None):
            total_to_repay += loan.total_to_repay
        if getattr(loan, "total_interest", None):
            total_interest_sum += loan.total_interest

    total_active_loans = len(loans)

    context = {
        "loans": loans,
        "kpi_total_loans": total_active_loans,
        "kpi_total_principal": total_principal,
        "kpi_total_to_repay": total_to_repay,
        "kpi_total_interest": total_interest_sum,
        "segment": "loans_active",
    }
    return render(request, "loan/active_loans_list.html", context)


#============================================================================================================
#============================================================================================================
@login_required
def active_loan_details(request, loan_id):
    """
    Devolve detalhes completos de um empréstimo activo em JSON
    para alimentar o modal com tabs.
    """
    loan = get_object_or_404(
        Loan.objects.select_related(
            "member",
            "loan_type",
            "interest_type",
            "approved_by",
            "created_by",
        ).prefetch_related(
            "disbursements",
            "disbursements__company_account",
            "loan_guarantors",
            "loan_guarantors__guarantor",
            "guarantees",
            "member__client_accounts",
            "member__client_accounts__account_type",
        ),
        pk=loan_id,
        status="disbursed",
    )

    # cálculo juros / total a reembolsar
    total_to_repay = None
    total_interest = None
    if loan.payment_per_period and loan.term_periods:
        total_to_repay = loan.payment_per_period * loan.term_periods
        total_interest = total_to_repay - loan.principal_amount

    member = loan.member

    # último desembolso
    last_disb = loan.disbursements.order_by("-disburse_date", "-id").first()

    # contas do cliente
    client_accounts_data = []
    for ca in member.client_accounts.filter(is_active=True).select_related("account_type"):
        client_accounts_data.append({
            "id": ca.id,
            "account_type": ca.account_type.get_category_display(),
            "account_type_name": ca.account_type.name,
            "identifier": ca.account_identifier,
            "balance": float(ca.balance),
        })

    # fiadores
    guarantors_data = []
    for g in loan.loan_guarantors.select_related("guarantor"):
        guarantors_data.append({
            "id": g.id,
            "name": str(g.guarantor),
            "phone": g.guarantor.phone,
            "account_number": g.account_number,
            "amount": float(g.amount) if g.amount is not None else None,
        })

    # garantias
    guarantees_data = []
    for gg in loan.guarantees.all():
        guarantees_data.append({
            "id": gg.id,
            "name": gg.name,
            "guarantee_type": gg.guarantee_type,
            "serial_number": gg.serial_number,
            "estimated_price": float(gg.estimated_price) if gg.estimated_price is not None else None,
            "description": gg.description,
            "attachment_url": gg.attachment.url if gg.attachment else None,
        })

    data = {
        "loan": {
            "id": loan.id,
            "status": loan.status,
            "loan_type": loan.loan_type.name if loan.loan_type else None,
            "interest_type": loan.interest_type.name if loan.interest_type else None,
            "principal_amount": float(loan.principal_amount),
            "term_periods": loan.term_periods,
            "period_type": loan.period_type,
            "payment_per_period": float(loan.payment_per_period) if loan.payment_per_period else None,
            "total_to_repay": float(total_to_repay) if total_to_repay is not None else None,
            "total_interest": float(total_interest) if total_interest is not None else None,
            "release_date": loan.release_date.isoformat() if loan.release_date else None,
            "first_payment_date": loan.first_payment_date.isoformat() if loan.first_payment_date else None,
            "disburse_method": loan.disburse_method,
            "purpose": loan.purpose,
            "remarks": loan.remarks,
            "created_at": loan.created_at.isoformat() if loan.created_at else None,
            "created_by": loan.created_by.get_full_name() if loan.created_by else None,
            "approved_by": loan.approved_by.get_full_name() if loan.approved_by else None,
        },
        "member": {
            "id": member.id,
            "name": str(member),
            "phone": member.phone,
            "alt_phone": member.alt_phone,
            "email": member.email,
            "city": member.city,
            "address": member.address,
            "profession": member.profession,
            "manager": member.manager.get_full_name() if member.manager else None,
        },
        "disbursement": {
            "exists": last_disb is not None,
            "amount": float(last_disb.amount) if last_disb else None,
            "date": last_disb.disburse_date.isoformat() if last_disb else None,
            "method": last_disb.method if last_disb else None,
            "company_account": last_disb.company_account.name if last_disb and last_disb.company_account else None,
            "company_account_identifier": last_disb.company_account.account_identifier
                if last_disb and last_disb.company_account else None,
            "attachment_url": last_disb.attachment.url if last_disb and last_disb.attachment else None,
            "notes": last_disb.notes if last_disb else None,
        },
        "client_accounts": client_accounts_data,
        "guarantors": guarantors_data,
        "guarantees": guarantees_data,
    }

    return JsonResponse(data, safe=False)

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