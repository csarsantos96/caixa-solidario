import { summarizeWeights } from './weights.js';

// Keep the same column count as the detailed sales export.
export function weightSummaryCsvRows(sales) {
    const summary = summarizeWeights(sales);
    const pad = row => [...row, ...Array(14 - row.length).fill('')];
    const kg = row => row.qty === row.unknown ? 'Não informado' : (row.grams / 1000).toFixed(3).replace('.', ',');
    const headings = ['Produto / alimento', 'Quantidade total (unidades)', 'Peso por unidade (g)', 'Peso total conhecido (kg)', 'Unidades sem peso', 'Receita (R$)'];
    const row = (item, unitWeight = '') => pad([
        item.name, item.qty, unitWeight, kg(item), item.unknown,
        (item.revenue / 100).toFixed(2).replace('.', ','),
    ]);
    return [
        pad([]), pad(['RESUMO POR ALIMENTO — SOMENTE VENDAS PAGAS NO PERÍODO']),
        pad(headings), ...summary.foods.map(item => row(item)),
        pad([]), pad(['RESUMO POR EMBALAGEM — SOMENTE VENDAS PAGAS NO PERÍODO']),
        pad(headings), ...summary.products.map(item => row(item, item.unitWeight ?? 'Não informado')),
        pad(['TOTAL GERAL — VENDAS PAGAS', summary.units, '',
            summary.units > 0 && summary.units === summary.unknown ? 'Não informado' : (summary.grams / 1000).toFixed(3).replace('.', ','),
            summary.unknown, (summary.foods.reduce((total, item) => total + item.revenue, 0) / 100).toFixed(2).replace('.', ',')]),
    ];
}
