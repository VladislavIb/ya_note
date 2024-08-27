from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestLogic(TestCase):
    """Тесты логики приложения."""

    NEW_NOTE_DATA = {
        'title': 'Новая заметка',
        'text': 'Текст новой заметки',
        'slug': 'new-note'
    }

    UPDATE_NOTE_DATA = {
        'title': 'Обновленная заметка',
        'text': 'Текст обновленной заметки',
        'slug': 'updated-note'
    }

    OTHER_NOTE_DATA = {
        'title': 'Другая заметка',
        'text': 'Текст другой заметки',
        'slug': 'other-note'
    }

    SUCCESS_URL = reverse('notes:success')
    LOGIN_URL = '/auth/login/?next='

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
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='test-slug',
            author=cls.user
        )
        cls.other_note = Note.objects.create(
            title='Другой заголовок',
            text='Другой текст',
            slug='other-slug',
            author=cls.other_user
        )

    def setUp(self):
        """Логин авторизованного пользователя."""
        self.client.login(username='testuser', password='testpass')

    def test_anonymous_user_cannot_create_note(self):
        """Анонимный пользователь не может создавать заметку."""
        self.client.logout()
        response = self.client.post(reverse('notes:add'), self.NEW_NOTE_DATA)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, f'{self.LOGIN_URL}/add/')

    def test_authenticated_user_can_create_note(self):
        """Авторизованный пользователь может создавать заметку."""
        response = self.client.post(reverse('notes:add'), self.NEW_NOTE_DATA)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.SUCCESS_URL)
        self.assertTrue(Note.objects.filter(slug='new-note').exists())

    def test_authenticated_user_can_edit_own_note(self):
        """Авторизованный пользователь может редактировать свою заметку."""
        response = self.client.post(
            reverse('notes:edit', args=[self.note.slug]),
            self.UPDATE_NOTE_DATA
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.SUCCESS_URL)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.UPDATE_NOTE_DATA['title'])
        self.assertEqual(self.note.text, self.UPDATE_NOTE_DATA['text'])

    def test_authenticated_user_cannot_edit_other_user_note(self):
        """Авторизованный пользователь не может редактировать чужую заметку."""
        response = self.client.post(
            reverse('notes:edit', args=[self.other_note.slug]),
            self.OTHER_NOTE_DATA
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_authenticated_user_can_delete_own_note(self):
        """Авторизованный пользователь может удалять свою заметку."""
        response = self.client.post(
            reverse('notes:delete', args=[self.note.slug])
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.SUCCESS_URL)
        self.assertFalse(Note.objects.filter(slug=self.note.slug).exists())

    def test_authenticated_user_cannot_delete_other_user_note(self):
        """Авторизованный пользователь не может удалять чужую заметку."""
        response = self.client.post(
            reverse('notes:delete', args=[self.other_note.slug])
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_cannot_create_note_with_duplicate_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        response = self.client.post(reverse('notes:add'), self.NEW_NOTE_DATA)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.client.post(reverse('notes:add'), self.NEW_NOTE_DATA)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(
            response, 'form', 'slug',
            'new-note - такой slug уже существует, '
            'придумайте уникальное значение!'
        )
        self.assertEqual(Note.objects.filter(slug='new-note').count(), 1)

    def test_slug_is_generated_if_not_provided(self):
        """Если slug не передан, он будет сгенерирован автоматически."""
        data = {
            'title': 'Новая заметка без slug',
            'text': 'Тест новой заметки',
        }
        expected_slug = slugify(data['title'])
        response = self.client.post(reverse('notes:add'), data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Note.objects.filter(slug=expected_slug).exists())
