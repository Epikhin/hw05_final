
from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..views import CONST_POST

from ..models import Group, Post, User

CONST_POST1 = 3
CONST_POST2 = 13


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='qwerty')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': 'qwerty'}
                    ): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': '1'}
                    ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:group_list', kwargs={'slug': 'slug_slug'}
                    ): 'posts/group_list.html',
            reverse('posts:post_edit', kwargs={'post_id': '1'}
                    ): 'posts/post_create.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self._assert_post(first_object)

    def _assert_post(self, first_object):
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.slug, self.group.slug)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'slug_slug'}))
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        self.assertTrue(post_text_0, 'Тестовая запись для создания 2 поста')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'slug_slug'}))
        first_object = response.context['page_obj'][0]
        self._assert_post(first_object)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'qwerty'}))
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.author
        self._assert_post(first_object)
        self.assertEqual(post_group_0, PostViewsTests.post.author)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        first_object = response.context['post']
        self.assertEqual(first_object.pk, PostViewsTests.post.pk)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        with_cache = response.content
        first_post = Post.objects.get(id=1)
        first_post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        after_delete_bd = response.content
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        after_clean_cache = response.content
        self.assertEqual(with_cache, after_delete_bd, 'Ошибка')
        self.assertNotEqual(after_delete_bd, after_clean_cache, 'Ошибка')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='saint')
        cls.group1 = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(CONST_POST2):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group1
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()


    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), CONST_POST)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), CONST_POST1)

    def test_first_page_group_list_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'slug_slug'}))
        self.assertEqual(len(response.context['page_obj']), CONST_POST)

    def test_first_page_profile_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'saint'}))
        self.assertEqual(len(response.context['page_obj']), CONST_POST)
