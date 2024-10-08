from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты для проверки маршрутов приложения notes."""

    LOGIN_URL = '/auth/login/'
    SUCCESS_URL = reverse('notes:success')

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

    def login_user(self, user):
        """Логин пользователя."""
        return self.client.login(username=user.username, password='testpass')

    def test_pages_accessibility(self):
        """Проверка доступности страниц для всех пользователей."""
        pages = [
            ('notes:home', None, HTTPStatus.OK, None),
            ('notes:detail', [self.note.slug], HTTPStatus.OK, self.user),
            ('notes:edit', [self.note.slug], HTTPStatus.OK, self.user),
            ('notes:delete', [self.note.slug], HTTPStatus.OK, self.user),
            ('notes:add', None, HTTPStatus.OK, self.user),
            ('notes:success', None, HTTPStatus.OK, self.user),
            ('notes:list', None, HTTPStatus.OK, self.user),
            ('users:signup', None, HTTPStatus.OK, None),
            ('users:login', None, HTTPStatus.OK, None),
            ('users:logout', None, HTTPStatus.OK, self.user),
        ]

        for name, args, expected_status, user in pages:
            with self.subTest(name=name):
                if user:
                    self.login_user(user)
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, expected_status)

    def test_redirect_anonymous_user(self):
        """Проверка редиректа анонима на страницу авторизации."""
        redirects = [
            (
                'notes:edit',
                [self.note.slug],
                f'{self.LOGIN_URL}?next=/edit/{self.note.slug}/'
            ),
            (
                'notes:delete',
                [self.note.slug],
                f'{self.LOGIN_URL}?next=/delete/{self.note.slug}/'
            ),
            ('notes:add', None, f'{self.LOGIN_URL}?next=/add/'),
            ('notes:list', None, f'{self.LOGIN_URL}?next=/notes/'),
            ('notes:success', None, f'{self.LOGIN_URL}?next=/done/'),
        ]

        for name, args, expected_redirect in redirects:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertRedirects(response, expected_redirect)

    def test_non_author_cannot_access_restricted_pages(self):
        """Недоступность редактирования и удаления чужих заметок."""
        restricted_pages = [
            ('notes:edit', [self.note.slug]),
            ('notes:delete', [self.note.slug]),
        ]

        self.client.login(username='otheruser', password='otherpass')

        for name, args in restricted_pages:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_note_success_page_accessibility(self):
        """Страница успеха доступна авторизованному пользователю."""
        self.login_user(self.user)
        response = self.client.get(self.SUCCESS_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_after_login(self):
        """Проверка перенаправления пользователя после успешного входа."""
        login_url_with_next = f'{self.LOGIN_URL}?next=/edit/{self.note.slug}/'
        response = self.client.get(
            reverse('notes:edit', args=[self.note.slug])
        )
        self.assertRedirects(response, login_url_with_next)
        response = self.client.post(
            login_url_with_next,
            data={'username': 'testuser', 'password': 'testpass'},
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('notes:edit', args=[self.note.slug])
        )

    def test_incorrect_slug_redirects(self):
        """Некорректный slug должен привести к перенаправлению."""
        response = self.client.get(
            reverse('notes:detail', args=['wrong-slug'])
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(response.url.startswith('/'))

    def test_notes_list_accessible_by_author(self):
        """Страница списка заметок доступна автору и отображает его заметки."""
        self.login_user(self.user)
        response = self.client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.note.title)
        self.assertNotContains(response, self.other_note.title)
