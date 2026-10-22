import test from 'node:test';
import assert from 'node:assert/strict';
import { thermalReceiptHtml, openThermalReceipt } from './thermalReceipt.js';

const sale = {
    id: 'sale-123', status: 'paid', event: 'Evento <teste>',
    customer: '<script>alert(1)</script>', method: 'Pix & cartão',
    createdAt: '2026-10-19T15:00:00+00:00', total: 2400,
    items: JSON.stringify([{ name: 'Arroz <especial>', qty: 3, price: 750 }]),
};

test('thermal receipt uses saved amounts, escapes content and retains voucher at both widths', () => {
    for (const width of ['58', '80']) {
        const html = thermalReceiptHtml(sale, width);
        assert.ok(html.includes(`width:${width}mm`));
        assert.ok(html.includes('Evento &lt;teste&gt;'));
        assert.ok(html.includes('Arroz &lt;especial&gt;'));
        assert.ok(!html.includes('<script>'));
        assert.ok(html.includes('Pix &amp; cartão'));
        assert.match(html, /3 × R\$\s7,50/);
        assert.match(html, /R\$\s22,50/);
        assert.match(html, /R\$\s1,50/);
        assert.match(html, /R\$\s24,00/);
        assert.ok(html.includes('19/10/2026, 10:00'));
        assert.ok(html.includes('CS-sale-123'));
    }
});

test('rejects unpaid sales and invalid paper widths before opening a window', () => {
    for (const status of ['pending', 'cancelled']) {
        assert.throws(() => openThermalReceipt({ ...sale, status }, '80', () => assert.fail('window opened')), /venda paga/);
    }
    assert.throws(() => thermalReceiptHtml(sale, '80;bad'), /58 ou 80/);
});

test('reports blocked popups and prepares an isolated printable document', () => {
    assert.throws(() => openThermalReceipt(sale, '80', () => null), /Permita abrir janelas/);
    let written = '', closed = false;
    const popup = { opener: {}, document: { write: html => { written = html; }, close: () => { closed = true; } } };
    openThermalReceipt(sale, '58', () => popup);
    assert.equal(popup.opener, null);
    assert.ok(written.includes('CS-sale-123'));
    assert.equal(closed, true);
});
