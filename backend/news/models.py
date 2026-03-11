from django.conf import settings
from django.db import models


class News(models.Model):
    news_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=300)
    content = models.TextField()
    source_url = models.URLField(unique=True)
    created_at = models.DateField(help_text="복지로 기사 게시일")
    fetched_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-created_at", "-fetched_at"]

    def __str__(self) -> str:
        return str(self.title)


class NewsComment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="news_comments",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.user} on {self.news.news_id}"


class NewsFetchStatus(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILURE = "failure"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "성공"),
        (STATUS_FAILURE, "실패"),
    ]

    fetch_date = models.DateField(unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        verbose_name = "뉴스 수집 상태"
        verbose_name_plural = "뉴스 수집 상태"

    def __str__(self) -> str:
        return f"{self.fetch_date}: {self.status}"
