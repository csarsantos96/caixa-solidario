import { Bean, Coffee, Droplets, Flower2, Milk, Package, Wheat } from 'lucide-react';

function productStyle(name, category = '') {
    const text = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    if (text.includes('macarrao')) return { Icon: Wheat, label: 'MASSA', color: '#b87526', fill: '#fff0c9' };
    if (text.includes('cafe')) return { Icon: Coffee, label: 'CAFÉ', color: '#7a4d38', fill: '#f3e0cf' };
    if (text.includes('oleo')) return { Icon: Droplets, label: 'ÓLEO', color: '#a68118', fill: '#fff0ac', bottle: true };
    if (text.includes('feijao')) return { Icon: Bean, label: 'FEIJÃO', color: '#984e42', fill: '#f7ded4' };
    if (text.includes('arroz')) return { Icon: Wheat, label: 'ARROZ', color: '#39769b', fill: '#e0eff9' };
    if (text.includes('leite')) return { Icon: Milk, label: 'LEITE', color: '#497ead', fill: '#e2efff' };
    if (text.includes('farinha')) return { Icon: Wheat, label: 'FARINHA', color: '#9b7940', fill: '#f6ead5' };
    if (/flocao|cuscuz|milho/.test(text)) return { Icon: Wheat, label: 'MILHO', color: '#aa791e', fill: '#fff1bb' };
    if (/absorvente|protetor/.test(text) || category.toLowerCase() === 'higiene') return { Icon: Flower2, label: 'HIGIENE', color: '#8b5b9f', fill: '#f2e3f9' };
    return { Icon: Package, label: 'PRODUTO', color: '#456d99', fill: '#e2ecf8' };
}

export default function ProductArt({ name, category }) {
    const { Icon, label, color, fill, bottle } = productStyle(name, category);
    return <svg className="product-illustration" viewBox="0 0 160 120" aria-hidden="true" focusable="false">
        <ellipse cx="80" cy="111" rx="40" ry="5" fill={color} opacity=".12"/>
        {bottle ? <>
            <rect x="68" y="6" width="24" height="13" rx="3" fill={color}/>
            <path d="M69 19h22v16l14 17v48a8 8 0 0 1-8 8H63a8 8 0 0 1-8-8V52l14-17Z" fill={fill} stroke={color} strokeWidth="2"/>
        </> : <>
            <path d="M47 12h66l-5 14 7 73a8 8 0 0 1-8 9H53a8 8 0 0 1-8-9l7-73Z" fill={fill} stroke={color} strokeWidth="2"/>
            <path d="M50 20h60M49 100h62" stroke={color} opacity=".35" strokeWidth="3"/>
        </>}
        <rect x="54" y="40" width="52" height="51" rx="6" fill="white" opacity=".85"/>
        <Icon x="67" y="45" width="26" height="26" color={color} strokeWidth="1.7"/>
        <text x="80" y="84" textAnchor="middle" fill={color} fontSize="8" fontFamily="Arial, sans-serif" fontWeight="700" letterSpacing=".5">{label}</text>
    </svg>;
}
