import test from 'node:test';
import assert from 'node:assert/strict';
import { weightFromName, summarizeWeights, kilograms } from './weights.js';
import { weightSummaryCsvRows } from './weightCsv.js';

test('CSV includes product totals across sales, package totals and unknown weights', () => {
    const sale = (status, items) => ({ status, items: JSON.stringify(items) });
    const pasta = { id: 'pasta', name: 'Macarrão — 500 g', qty: 3, price: 100 };
    const rows = weightSummaryCsvRows([
        sale('paid', [pasta]), sale('paid', [{ ...pasta, qty: 1 },
            { id: 'large', name: 'Macarrão — 1 kg', qty: 2, price: 200 },
            { id: 'milk', name: 'Leite em pó', qty: 1, price: 500 }]),
        sale('cancelled', [{ ...pasta, qty: 100 }]),
    ]);
    assert.ok(rows.every(row => row.length === 14));
    assert.deepEqual(rows.find(row => row[0] === 'Macarrão').slice(0, 6), ['Macarrão', 6, '', '4,000', 0, '8,00']);
    assert.deepEqual(rows.find(row => row[0] === pasta.name).slice(0, 6), [pasta.name, 4, 500, '2,000', 0, '4,00']);
    assert.equal(rows.find(row => row[0] === 'Leite em pó')[3], 'Não informado');
    assert.deepEqual(rows.at(-1).slice(1, 5), [7, '', '4,000', 1]);
});

test('recognizes grams and decimal kilograms without treating volume as mass', () => {
    assert.equal(weightFromName('Macarrão — 500 g'), 500);
    assert.equal(weightFromName('Arroz 1,5 kg'), 1500);
    assert.equal(weightFromName('Café 0.25 KG'), 250);
    assert.equal(weightFromName('Óleo — 900 ml'), null);
    assert.equal(weightFromName('Leite em pó'), null);
    assert.equal(kilograms(3500), '3,5 kg');
});

test('groups package sizes and excludes pending or cancelled sales', () => {
    const sales = [{ status: 'paid', items: JSON.stringify([
        { id: 'pasta500', name: 'Macarrão — 500 g', qty: 3, price: 100 },
        { id: 'pasta1000', name: 'Macarrão — 1 kg', qty: 2, price: 200 },
        { id: 'coffee', name: 'Café — 500 g', qty: 4, price: 300, weight_grams: 500 },
        { id: 'milk', name: 'Leite em pó', qty: 2, price: 400 },
    ]) }, ...['pending', 'cancelled'].map(status => ({ status, items: JSON.stringify([
        { id: 'pasta500', name: 'Macarrão — 500 g', qty: 100, price: 100 },
    ]) }))];
    const result = summarizeWeights(sales);
    const pasta = result.foods.find(row => row.name === 'Macarrão');
    assert.equal(pasta.qty, 5);
    assert.equal(pasta.grams, 3500);
    assert.equal(pasta.revenue, 700);
    assert.equal(result.foods.find(row => row.name === 'Café').grams, 2000);
    assert.equal(result.products.length, 4);
    assert.equal(result.grams, 5500);
    assert.equal(result.unknown, 2);
    assert.equal(result.units, 11);
});

test('saved weights take precedence over names and unknown stays unknown', () => {
    const result = summarizeWeights([{ status: 'paid', items: JSON.stringify([
        { id: 'a', name: 'Café — 500 g', weight_grams: 250, qty: 2, price: 100 },
        { id: 'b', name: 'Café — 500 g', weight_grams: null, qty: 3, price: 100 },
    ]) }]);
    assert.equal(result.grams, 500);
    assert.equal(result.unknown, 3);
    assert.equal(result.foods[0].qty, 5);
});
