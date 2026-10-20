const massLabel = /(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(kg|g)\b/i;

export function weightFromName(name) {
    const match = name.match(massLabel);
    if (!match) return null;
    const grams = Number(match[1].replace(',', '.')) * (match[2].toLowerCase() === 'kg' ? 1000 : 1);
    return Number.isInteger(grams) && grams > 0 ? grams : null;
}

export function itemWeight(item) {
    // New sales keep the original weight, including an explicitly unknown weight.
    return Object.hasOwn(item, 'weight_grams') ? item.weight_grams : weightFromName(item.name);
}

export const kilograms = grams => (grams / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 3 }) + ' kg';

export function summarizeWeights(sales) {
    const products = new Map();
    const foods = new Map();
    let grams = 0, unknown = 0, units = 0;
    for (const sale of sales.filter(s => s.status === 'paid')) {
        for (const item of JSON.parse(sale.items)) {
            const weight = itemWeight(item);
            const food = item.name.replace(massLabel, '').replace(/[\s—–-]+$/g, '').trim() || item.name;
            const productKey = JSON.stringify([item.id, item.name, weight]);
            for (const [map, key, name] of [[products, productKey, item.name], [foods, food.toLocaleLowerCase('pt-BR'), food]]) {
                const row = map.get(key) || { name, qty: 0, grams: 0, unknown: 0, revenue: 0, unitWeight: weight };
                row.qty += item.qty;
                row.revenue += item.qty * item.price;
                if (weight == null) row.unknown += item.qty;
                else row.grams += item.qty * weight;
                map.set(key, row);
            }
            units += item.qty;
            if (weight == null) unknown += item.qty;
            else grams += item.qty * weight;
        }
    }
    return { products: [...products.values()], foods: [...foods.values()], grams, unknown, units };
}
