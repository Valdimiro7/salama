from django.shortcuts import render

def dashboard_view(request):
    context = {
        "page_title": "Salama · Microcrédito",
        "total_carteira": 0,
        "total_clientes": 0,
        "total_em_atraso": 0,
        "taxa_recuperacao": 0,
    }
    # usa o template dentro da pasta core/
    return render(request, "dashboard.html", context)
