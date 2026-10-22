from test_api import sale


def test_events_require_login_and_validate_names(client, auth):
    assert auth.post('/api/events', json={'name': '   '}).status_code == 422
    assert auth.post('/api/events', json={'name': 'x' * 121}).status_code == 422
    auth.post('/api/logout')
    assert client.post('/api/events', json={'name': 'Privado'}).status_code == 401


def test_persist_empty_events_and_filter_historic_sales(auth, rice):
    assert auth.post('/api/events', json={'name': ' Próximo evento '}).json()['name'] == 'Próximo evento'
    assert auth.post('/api/events', json={'name': 'Próximo evento'}).status_code == 200
    assert auth.post('/api/sales', json=sale(id='a', event='Anterior')).status_code == 200
    assert auth.post('/api/sales', json=sale(id='b', event='Outro')).status_code == 200
    data = auth.get('/api/data').json()
    assert {'Anterior', 'Outro', 'Próximo evento'} <= set(data['events'])
    assert data['events'].count('Próximo evento') == 1
    assert [s['id'] for s in auth.get('/api/data', params={'event': 'Anterior'}).json()['sales']] == ['a']
    assert auth.get('/api/data', params={'event': 'Próximo evento'}).json()['sales'] == []
    assert len(auth.get('/api/data').json()['sales']) == 2
