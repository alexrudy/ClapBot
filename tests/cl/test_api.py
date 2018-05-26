def test_image(client, image):
    response = client.get(f'/image/{image}/full.jpg')
    assert response.status_code == 200
