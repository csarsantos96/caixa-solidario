from app.weights import weight_from_name


def test_mass_labels():
    assert weight_from_name('Macarrão — 500 g') == 500
    assert weight_from_name('Arroz 1,5 kg') == 1500
    assert weight_from_name('Café 0.25 KG') == 250
    assert weight_from_name('Óleo — 900 ml') is None
    assert weight_from_name('Leite em pó') is None


def test_weight_is_saved_with_sale(auth, rice):
    product = {**rice, 'weight_grams': 500}
    assert auth.post('/api/products', json=product).status_code == 200
    payload = {'id': 'weighted-sale', 'items': [{'id': rice['id'], 'qty': 3}],
               'event': 'Evento', 'status': 'paid', 'method': 'Pix'}
    assert auth.post('/api/sales', json=payload).status_code == 200
    assert auth.post('/api/products', json={**product, 'weight_grams': 1000}).status_code == 200
    import json
    saved = next(s for s in auth.get('/api/data').json()['sales'] if s['id'] == payload['id'])
    assert json.loads(saved['items'])[0]['weight_grams'] == 500


def test_invalid_weights(auth, rice):
    for value in [0, -1, 0.5, '500', 1_000_001]:
        assert auth.post('/api/products', json={**rice, 'weight_grams': value}).status_code == 422
