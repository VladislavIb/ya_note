from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from notes.models import Note


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.note = Note.objects.create(title='Заголовок', text='Текст',)

    def test_pages_availability(self):
        """Проверка доступности страниц."""
        urls = (
            ('notes:home', None),
            ('notes:detail', (self.note.id,)),

        )

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)