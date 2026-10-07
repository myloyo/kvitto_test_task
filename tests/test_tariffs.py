def test_list_tariffs_returns_three_prices_in_kopecks(client):
    response = client.get("/tariffs")
    assert response.status_code == 200

    tariffs = response.json()
    by_id = {item["id"]: item for item in tariffs}

    assert set(by_id) == {"basic", "standard", "premium"}
    assert by_id["basic"] == {"id": "basic", "title": "Basic", "price": 990_000}
    assert by_id["standard"]["price"] == 1_990_000
    assert by_id["premium"]["price"] == 2_990_000
    assert all(isinstance(item["price"], int) for item in tariffs)
