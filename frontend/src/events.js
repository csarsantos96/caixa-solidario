export function eventSales(sales, event) {
    return sales.filter(sale => sale.event === event);
}

export function eventNames(registered, sales, current) {
    return [...new Set([...registered, ...sales.map(sale => sale.event), current])].filter(Boolean).sort((a, b) => a.localeCompare(b, 'pt-BR'));
}
