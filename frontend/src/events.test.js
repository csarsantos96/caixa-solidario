import test from 'node:test';
import assert from 'node:assert/strict';
import { eventNames, eventSales } from './events.js';
import { summarizeWeights } from './weights.js';

test('event selection isolates sales, revenue and food totals even on the same date', () => {
    const sales = [
        { event: 'A', total: 1500, status: 'paid', items: JSON.stringify([{ name: 'Arroz 1 kg', qty: 2, price: 750 }]) },
        { event: 'B', total: 7500, status: 'paid', items: JSON.stringify([{ name: 'Arroz 1 kg', qty: 10, price: 750 }]) },
    ];
    const filtered = eventSales(sales, 'A');
    assert.equal(filtered.length, 1);
    assert.equal(filtered.reduce((sum, sale) => sum + sale.total, 0), 1500);
    assert.equal(summarizeWeights(filtered).grams, 2000);
    assert.deepEqual(eventSales(sales, 'Novo'), []);
    assert.deepEqual(eventNames(['Novo', 'A'], sales, 'Antigo'), ['A', 'Antigo', 'B', 'Novo']);
});
