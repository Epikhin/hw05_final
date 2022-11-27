from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User
from django.core.files.uploadedfile import SimpleUploadedFile


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='qwerty')
        cls.form = PostForm()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='slug_slug2',
            description='Тестовое описание2',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        post_data = {
            'text': 'изменился',
            'group': PostFormTests.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_data,
            follow=True
        )
        text = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(text.text, post_data['text'])
        self.assertEqual(text.group.id, post_data['group'])

    def test_post_edit_by_not_author(self):
        author = User.objects.create_user(username='vvv')
        group = Group.objects.create(
            title='Тестовая группа2',
            slug='slug_slug3',
            description='Тестовое описание2',
        )
        post1 = Post.objects.create(
            author=author,
            text='abc',
            group=group
        )
        post_data = {
            'text': 'Редактирование поста',
            'group': self.group.id,
            'author': self.user
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post1.id}),
            data=post_data,
            follow=True
        )
        post1.refresh_from_db()
        self.assertRedirects(
            response, f'/posts/{post1.id}/'
        )
        self.assertNotEqual(post1.text, post_data['text'])
        self.assertNotEqual(post1.group.id, post_data['group'])
        self.assertNotEqual(post1.author, post_data['author'])

    def test_authorized_edit_post(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\00'
            b'\x01\x00\x80\x00\x00\x00\x00\00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\00'
            b'\x00\x00\x00\x2C\x00\x00\x00\00'
            b'\x02\x00\x01\x00\x00\x02\x02\0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_data = {
            'text': 'не измененные данные',
            'group': self.group.id,
            'image': uploaded,
        }
        post1 = Post.objects.create(
            author=self.user,
            text='измененные данные',
        )
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post1.id}),
            data=post_data,
            follow=True
        )
        post1.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post1.text, post_data['text'])
        self.assertEqual(post1.group.id, post_data['group'])
        self.assertTrue(post1.image, post_data['image'])
