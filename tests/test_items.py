from fastapi.testclient import TestClient


def test_create_and_list_items(client: TestClient) -> None:
    created = client.post('/items', json={'name': 'first'})

    assert created.status_code == 200
    assert created.json() == {'id': 1, 'name': 'first'}
    assert client.get('/items').json() == [{'id': 1, 'name': 'first'}]


def test_get_item(client: TestClient) -> None:
    client.post('/items', json={'name': 'first'})

    response = client.get('/items/1')

    assert response.status_code == 200
    assert response.json() == {'id': 1, 'name': 'first'}


def test_get_missing_item_returns_404(client: TestClient) -> None:
    response = client.get('/items/999')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Item 999 not found'}


def test_create_duplicate_item_returns_409(client: TestClient) -> None:
    client.post('/items', json={'id': 7, 'name': 'first'})

    response = client.post('/items', json={'id': 7, 'name': 'second'})

    assert response.status_code == 409
    assert response.json() == {'detail': 'Item 7 already exists'}
    assert client.get('/items/7').json() == {'id': 7, 'name': 'first'}
