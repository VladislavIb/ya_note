"""Тесты маршрутов."""
from http import HTTPStatus

from django.urls import reverse


def test_home_availability_for_anonymous_user(client):
    """Анонимный пользователь видит главную страницу."""
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
