from datetime import datetime
from html import escape
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


def receipt_html(sale: Sale) -> str:
    """Render the saved sale snapshot, with escaped customer and catalog data."""
    date = datetime.fromisoformat(sale.created_at).astimezone(ZoneInfo("America/Rio_Branco"))
    rows = "".join(
        f'<tr><td style="padding:14px 0;border-bottom:1px solid #e3e9f0">'
        f'{item["qty"]} × {escape(item["name"])}'
        f'<br><small>{money(item["price"])} / unidade</small></td>'
        f'<td style="padding:14px 0;text-align:right;border-bottom:1px solid #e3e9f0">'
        f'{money(item["qty"] * item["price"])}</td></tr>'
        for item in sale.items
    )
    greeting = f'Olá, {escape(sale.customer)}!' if sale.customer else 'Obrigado pela sua compra!'
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#f3f6fb;font-family:Arial,sans-serif;color:#21334d">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fff;border:1px solid #e3e9f0;border-radius:16px">
<tr><td style="padding:28px;background:#173b69;color:#fff;border-radius:16px 16px 0 0">
<p style="margin:0;font-size:13px;letter-spacing:2px">BILHETE SOLIDÁRIO</p>
<h1 style="font-size:25px;margin:16px 0 8px">Seu recibo de compra</h1>
<p style="margin:0">{escape(sale.event)}</p></td></tr>
<tr><td style="padding:28px"><h2 style="font-size:19px">{greeting}</h2>
<p>Confira os itens da sua compra abaixo.</p>
<p style="font-size:12px;color:#64748b">Venda {escape(sale.id)}<br>{date:%d/%m/%Y às %H:%M} (Rio Branco)</p>
<table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px"><thead><tr>
<th align="left">Itens comprados</th><th align="right">Valor</th></tr></thead><tbody>{rows}</tbody></table>
<p style="padding:20px;background:#edf3fb;border-radius:8px;font-size:22px;color:#173b69">
Total pago: <strong>{money(sale.total)}</strong></p>
<p>Pagamento informado pelo operador: <strong>{escape(sale.method)}</strong><br>Situação: paga</p>
<div style="padding:20px;border:2px dashed #9bb2d1;border-radius:10px">
<strong>Voucher de entrada • 1 pessoa</strong><p>Apresente este voucher à recepção do SEBRAE.</p>
<p style="font-family:monospace;overflow-wrap:anywhere">CS-{escape(sale.id)}</p></div>
<p style="font-size:12px;color:#64748b;line-height:1.6">Recibo de venda sem valor fiscal.
Pagamento conferido pelo operador. Não substitui o comprovante bancário.</p>
</td></tr></table></td></tr></table></body></html>'''
