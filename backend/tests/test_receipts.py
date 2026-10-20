from types import SimpleNamespace

from app.receipts import receipt_html


def test_receipt_escapes_data_and_uses_saved_items():
    sale = SimpleNamespace(
        id='sale-123', created_at='2026-10-19T15:00:00+00:00',
        event='Evento <teste>', customer='<img src=x onerror=alert(1)>',
        method='Pix & cartão', total=2250,
        items=[{'name': 'Arroz <especial>', 'qty': 3, 'price': 750}],
    )
    html = receipt_html(sale)
    assert '<img' not in html
    assert '&lt;img' in html
    assert 'Evento &lt;teste&gt;' in html
    assert '3 × Arroz &lt;especial&gt;' in html
    assert 'R$ 7,50 / unidade' in html
    assert html.count('R$ 22,50') == 2
    assert '19/10/2026 às 10:00' in html
    assert 'CS-sale-123' in html
