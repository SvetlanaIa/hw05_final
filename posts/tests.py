from django.test import TestCase, override_settings
from django.test import Client
from django.contrib.auth.models import User
from .models import Post, Group, Follow, Comment
from django.urls import reverse
from django.http import HttpResponseRedirect, request, response
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key


TEST_CACHE = {
    "default": {
        "BACKEND":
        "django.core.cache.backends.dummy.DummyCache",
    }
}


class PostTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345")
        post_text = "You are talking about things I have not done yet in the past tense. It is driving me crazy!"
        self.post = Post.objects.create(text=post_text, author=self.user)

    # После публикации поста новая запись появляется на главной странице сайта (index), на персональной странице
    #  пользователя (profile), и на отдельной странице поста (post)

    def test_publishing_new_post(self):
        self.client.login(username="sarah", password="12345")
        post_text = "You are talking about things I have not done yet in the past tense. It is driving me crazy!"
        post_id = self.post.pk
        for url in("/", "/sarah/", f"/sarah/{post_id}/"):
            response = self.client.get(url)
            self.assertContains(response, post_text, count=1,
                                status_code=200, msg_prefix="", html=False)

    # Авторизованный пользователь может отредактировать свой пост и его содержимое изменится на всех связанных страницах

    def test_edit_post(self):
        self.client.login(username="sarah", password="12345")
        edit_post_text = "    You are talking about things I have not done yet in the past tense. It is driving me crazy!"
        post_id = self.post.pk
        self.post.text = edit_post_text
        self.post.save()
        for url in("/", "/sarah/", f"/sarah/{post_id}/"):
            response = self.client.get(url)
            self.assertContains(response, edit_post_text, count=1,
                                status_code=200, msg_prefix="", html=False)

    # Проверка страницы конкретной записи,главной страницы,страницы профайла и страницы группы: на странице есть тег <img>
    @override_settings(CACHES=TEST_CACHE)
    def test_img_post(self):
        self.client.login(username="sarah", password="12345")
        self.group = Group.objects.create(
            title="test", slug="test", description="test")
        with open("media/zkxZrC5FZ_Y.jpg", "rb") as fp:
            self.post = self.client.post(
                "/new/", {
                    "group": 1,
                    "text": "Text",
                    "image": fp},
                follow=True)

        for url in("", "/sarah/", "/sarah/2/", "/group/test/"):
            response = self.client.get(url, follow=True)
            self.assertContains(response, "<img", count=1,
                                status_code=200, msg_prefix="", html=False)

    # Проверка, что срабатывает защита от загрузки файлов не-графических форматов при создании нового поста
    @override_settings(CACHES=TEST_CACHE)
    def test_not_img_post(self):
        self.client.login(username="sarah", password="12345")
        self.group = Group.objects.create(
            title="test", slug="test", description="test")

        with open("media/test.txt", "rb") as fp:
            self.post = self.client.post(
                "/new/", {
                    "group": 1,
                    "text": "Text",
                    "image": fp},
                follow=True)

        for url in("", "/sarah/", "/sarah/1/", "/group/test/"):
            response = self.client.get(url, follow=True)
            self.assertContains(response, "<img", count=0,
                                status_code=200, msg_prefix="", html=False)

    # Проверка, что срабатывает защита от загрузки файлов не-графических форматов  при редактировании
    @override_settings(CACHES=TEST_CACHE)
    def test_not_img_post_edit(self):
        self.client.login(username="sarah", password="12345")
        self.group = Group.objects.create(
            title="test", slug="test", description="test")

        with open("media/test.txt", "rb") as fp:
            self.post = self.client.post(
                "/sarah/2/edit/", {"text": "fred", "image": fp}, follow=True)

        for url in("", "/sarah/", "/sarah/1/", "/group/test/"):
            response = self.client.get(url, follow=True)
            self.assertContains(response, "<img", count=0,
                                status_code=200, msg_prefix="", html=False)

    # Проверка работы кэша.

    def test_cache(self):
        # получить ключ кэша для кэшированного фрагмента шаблона
        key = make_template_fragment_key("index", [1])
        self.assertFalse(cache.get(key))  # объект отсутствует в кэше
        self.client.get("/")
        self.assertTrue(cache.get(key))  # объект появился в кэше

    # Новая запись пользователя появляется в ленте тех, кто на него подписан

    def test_follow_new_post(self):
        self.user2 = User.objects.create_user(
            username="sarah2", email="connor2.s@skynet.com", password="23456")
        self.client.login(username="sarah2", password="23456")
        response = self.client.get("/sarah/follow/", follow=True)
        self.client.logout()

        self.client.login(username="sarah", password="12345")
        post_text = "You are talking about things I have not done yet in the past tense. It is driving me crazy!"
        post_id = self.post.pk
        self.client.logout()

        self.client.login(username="sarah2", password="23456")
        response = self.client.get("/follow/", follow=True)
        self.assertContains(response, post_text, count=1,
                            status_code=200, msg_prefix="", html=False)

    # Новая запись пользователя не появляется в ленте тех, кто не подписан на него.

    def test_not_follow_new_post_(self):
        self.user2 = User.objects.create_user(
            username="sarah2", email="connor2.s@skynet.com", password="23456")

        self.client.login(username="sarah", password="12345")
        post_text = "You are talking about things I have not done yet in the past tense. It is driving me crazy!"
        post_id = self.post.pk
        self.client.logout()

        self.client.login(username="sarah2", password="23456")
        response = self.client.get("/follow/", follow=True)
        self.assertContains(response, post_text, count=0,
                            status_code=200, msg_prefix="", html=False)

    # Только авторизированный пользователь может комментировать посты.

    def test_comment(self):
        self.user2 = User.objects.create_user(
            username="sarah2", email="connor2.s@skynet.com", password="23456")

        self.client.login(username="sarah", password="12345")
        post_text = "You are talking about things I have not done yet in the past tense. It is driving me crazy!"
        post_id = self.post.pk
        self.post = Post.objects.create(text=post_text, author=self.user)

        self.client.logout()

        self.client.login(username="sarah2", password="23456")

        self.comment = Comment.objects.create(
            text="Hello!", author=self.user2, post=self.post)
        response = self.client.get(f"/sarah/2/", follow=True)
        self.assertContains(response, "Hello!", count=1,
                            status_code=200, msg_prefix="", html=False)

        self.client.logout()

        self.comment = Comment.objects.create(
            text="I want to sleep", author=self.user2, post=self.post)
        response = self.client.get(f"/sarah/2/", follow=True)
        self.assertContains(response, "I want to sleep", count=0,
                            status_code=200, msg_prefix="", html=False)
