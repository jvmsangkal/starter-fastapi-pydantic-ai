from fastapi.testclient import TestClient


def test_create_and_list_items(client: TestClient) -> None:
    created = client.post('/items', json={'name': 'first'})

    assert created.status_code == 200
    assert created.json() == {'id': 1, 'name': 'first'}
    assert client.get('/items').json() == [{'id': 1, 'name': 'first'}]
