const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const money = value => escape((value / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }));

export function thermalReceiptHtml(sale, width = '80') {
    if (!['58', '80'].includes(width)) throw new Error('Escolha uma bobina de 58 ou 80 mm.');
    if (sale.status !== 'paid') throw new Error('O recibo térmico exige uma venda paga.');
    const items = JSON.parse(sale.items);
    const surcharge = Math.max(0, sale.total - items.reduce((sum, item) => sum + item.qty * item.price, 0));
    const date = new Date(sale.createdAt).toLocaleString('pt-BR', { timeZone: 'America/Rio_Branco', dateStyle: 'short', timeStyle: 'short' });
    return `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recibo ${escape(sale.id)}</title><style>
@page{size:auto;margin:0}*{box-sizing:border-box}body{margin:0;background:white;color:black;font:12px Arial,sans-serif}
article{width:${width}mm;padding:3mm;margin:0 auto;overflow-wrap:anywhere}h1{font-size:16px;margin:4px 0}h2{font-size:14px}header,.voucher,footer{text-align:center}p{margin:6px 0;line-height:1.4}
section{border-top:1px dashed black;margin-top:10px;padding-top:8px}.item{margin-bottom:8px;break-inside:avoid}.amount{display:flex;justify-content:space-between;gap:6px}.amount strong{flex-shrink:0}.total{font-size:16px;margin-top:8px}small{font-size:10px}.code{font-family:monospace;font-size:12px;word-break:break-all}.controls{max-width:400px;margin:16px auto;padding:12px;font:14px Arial,sans-serif}button{padding:12px;cursor:pointer}
@media print{.controls{display:none}article{margin:0}body{width:${width}mm}}
</style></head><body><div class="controls"><button onclick="window.print()">Imprimir recibo</button><p>Selecione a impressora térmica e papel de ${width} mm. Use escala de 100%, margens zero e desative cabeçalhos e rodapés.</p></div>
<article><header><b>BILHETE SOLIDÁRIO</b><h1>${escape(sale.event)}</h1><small>RECIBO DE VENDA • SEM VALOR FISCAL</small></header>
<section><p>Venda: ${escape(sale.id)}</p><p>${escape(date)} (Rio Branco)</p>${sale.customer ? `<p>Cliente: ${escape(sale.customer)}</p>` : ''}</section>
<section>${items.map(item => `<div class="item"><b>${escape(item.name)}</b><div class="amount"><span>${escape(item.qty)} × ${money(item.price)}</span><strong>${money(item.qty * item.price)}</strong></div></div>`).join('')}
${surcharge ? `<div class="amount"><span>Acréscimo do crédito</span><strong>${money(surcharge)}</strong></div>` : ''}
<div class="amount total"><b>Total pago</b><strong>${money(sale.total)}</strong></div><p>Pagamento: ${escape(sale.method)}</p><p>Situação: paga</p></section>
<section class="voucher"><h2>Voucher de entrada • 1 pessoa</h2><p>Apresente à recepção do SEBRAE.</p><p class="code">CS-${escape(sale.id)}</p><small>Reimpressões mantêm o mesmo voucher.</small></section>
<section><footer><small>Pagamento conferido pelo operador.<br>Não substitui o comprovante bancário.<br>Recibo sem valor fiscal.</small></footer></section></article></body></html>`;
}

export function openThermalReceipt(sale, width, openWindow = () => window.open('', '_blank', 'width=480,height=720')) {
    const html = thermalReceiptHtml(sale, width);
    const popup = openWindow();
    if (!popup) throw new Error('Permita abrir janelas para imprimir o recibo térmico.');
    popup.opener = null;
    popup.document.write(html);
    popup.document.close();
}
