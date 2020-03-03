from django.test import TestCase
from django.core import mail
from django.test import Client
from django.contrib.auth.models import User
from posts.models import Post, Follow


class UserLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345")
        post_text = "You are talking about things I have not done yet in the past tense. It is driving me crazy!"
        self.post = Post.objects.create(text=post_text, author=self.user)

    def test_send_email(self):
        mail.send_mail(
            "Тема письма", "Текст письма.",
            "from@rocknrolla.net", ["to@mailservice.com"],
            fail_silently=False,  # выводить описание ошибок
        )
       # Проверяем, что письмо лежит в исходящих
        self.assertEqual(len(mail.outbox), 1)
       # Проверяем, что тема первого письма правильная.
        self.assertEqual(mail.outbox[0].subject, "Тема письма")

    # После регистрации пользователя создается его персональная страница (profile)
    def test_profile(self):
        response = self.client.get("/sarah/")
        self.assertEqual(response.status_code, 200)

    # Авторизованный пользователь может опубликовать пост (new)
    def test_new_post(self):
        self.client.login(username="sarah", password="12345")
        response = self.client.get("/sarah/")
        self.assertEqual(len(response.context["posts"]), 1)

    # Неавторизованный посетитель не может опубликовать пост
    #  (его редиректит на страницу входа)
    def test_new_post_anonim(self):
        response = self.client.get("/new/", follow=True)
        self.assertRedirects(
            response, "/auth/login/?next=/new/", status_code=302)

    # Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок.
    def test_follow(self):
        self.user2 = User.objects.create_user(
            username="sarah2", email="connor2.s@skynet.com", password="23456")
        self.client.login(username="sarah2", password="23456")
        
        response = self.client.get("/sarah/follow/", follow=True)
        followers = Follow.objects.filter(author=self.user).count()
        self.assertEqual(followers, 1)
        
        response = self.client.get("/sarah/unfollow/", follow=True)
        followers = Follow.objects.filter(author=self.user).count()
        self.assertEqual(followers, 0)
