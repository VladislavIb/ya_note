from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    """Тесты для проверки контента на страницах приложения notes."""

    @classmethod
    def setUpTestData(cls):
        """Создание пользователей и заметок для использования в тестах."""
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        cls.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass'
        )
        cls.note1 = Note.objects.create(
            title='Первая заметка',
            text='Текст первой заметки',
            slug='first-note',
            author=cls.user
        )
        cls.note2 = Note.objects.create(
            title='Вторая заметка',
            text='Текст второй заметки',
            slug='second-note',
            author=cls.user
        )

    def setUp(self):
        """Логин пользователя."""
        self.client.login(username='testuser', password='testpass')

    def test_anonymous_user_cannot_see_submit_form(self):
        """Анонимный пользователь не видит форму отправки заметки."""
        self.client.logout()
        response = self.client.get(
            reverse('notes:detail', args=[self.note1.slug])
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/auth/login/?next=/note/{self.note1.slug}/'
        )

    def test_authenticated_user_can_see_submit_form_on_create(self):
        """Авторизованный пользователь видит форму создания заметки."""
        response = self.client.get(reverse('notes:add'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, '<form')

    def test_authenticated_user_can_see_submit_form_on_edit(self):
        """Авторизованный пользователь видит форму редактирования заметки."""
        response = self.client.get(
            reverse('notes:edit', args=[self.note1.slug])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, '<form')

    def test_notes_sorted_by_id(self):
        """Заметки на странице отсортированы по id (от старой к новой)."""
        response = self.client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        notes = response.context['note_list']
        self.assertGreater(notes[1].id, notes[0].id)

    def test_notes_are_in_object_list(self):
        """Заметки на странице присутствуют в списке заметок."""
        response = self.client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        notes = response.context['note_list']
        self.assertIn(self.note1, notes)
        self.assertIn(self.note2, notes)

    def test_notes_are_user_specific(self):
        """Заметки на странице принадлежат конкретному пользователю."""
        self.client.logout()
        self.client.login(username='otheruser', password='otherpass')
        other_user_note = Note.objects.create(
            title='Заметка другого пользователя',
            text='Текст заметки другого пользователя',
            slug='other-user-note',
            author=self.other_user
        )
        response = self.client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        notes = response.context['note_list']
        self.assertNotIn(self.note1, notes)
        self.assertNotIn(self.note2, notes)
        self.assertIn(other_user_note, notes)
