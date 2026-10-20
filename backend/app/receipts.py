from datetime import datetime
from zoneinfo import ZoneInfo
from .models import Sale

def money(value: int) -> str:
    return f"R$ {value // 100},{value % 100:02d}"

def receipt_text(sale: Sale) -> str:
    date = datetime.fromisoformat(sale.created_at).astimezone(ZoneInfo("America/Rio_Branco"))
    lines = [sale.event, "RECIBO DE VENDA — SEM VALOR FISCAL", f"Venda: {sale.id}",
             f"Voucher: CS-{sale.id}", f"Data: {date:%d/%m/%Y %H:%M}"]
    if sale.customer:
        lines.append(f"Cliente: {sale.customer}")
    lines += [f"{i['qty']} × {i['name']} — {money(i['qty'] * i['price'])}" for i in sale.items]
    lines += [f"Total pago: {money(sale.total)}", f"Pagamento informado pelo operador: {sale.method}",
              "Apresente o voucher à recepção do SEBRAE.",
              "Pagamento conferido manualmente. Recibo sem valor fiscal."]
    return "\n".join(lines)
