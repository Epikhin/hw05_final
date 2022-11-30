from http import HTTPStatus

from ..models import Group, Post, User
from django.test import TestCase, Client
from django.core.cache import cache


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='qwerty')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текстовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_task_list_url_uses_correct_template(self):
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_url_author(self):
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_private_url(self):
        """Без авторизации приватные URL недоступны"""
        url_names = (
            'create/',
            'posts/<int:post_id>/edit/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_status_code(self):
        url_status = {
            '/': 200,
            '/group/slug_slug/': 200,
            '/profile/qwerty/': 200,
            '/posts/1/': 200,
            '/unexisting_page/': 404,
        }
        for template, url in url_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(template)
                self.assertEqual(response.status_code, url)

    def test_new_for_authorized(self):
        """Страница /create доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous(self):
        """Страница /create перенаправляет анонима."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_follow_url(self):
        """Страница /follow доступна авторизованному пользователю."""
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница posts/<int:post_id>/edit/ перенаправляет анонима."""
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/edit/'))

    def test_create_url_redirect_anonymous(self):
        """Страница /create перенаправляет не авторизованного пользователя."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_posts_post_edit_url(self):
        """Страница posts/post_id/edit/ доступна только автору."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL адреса и шаблон"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
