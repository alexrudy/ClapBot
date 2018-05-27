from clapbot.cl import tasks


def test_image(client, craigslist, image):
    response = client.get(f'/image/{image}/full.jpg')
    assert response.status_code == 302

    tasks.download_image(image)

    response = client.get(f'/image/{image}/full.jpg')
    assert response.status_code == 200
