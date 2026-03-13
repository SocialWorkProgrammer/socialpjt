from django.db import models


class News(models.Model):
    news_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=300)
    content = models.TextField()
    source_url = models.URLField(unique=True)
    created_at = models.DateField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-fetched_at"]

    def __str__(self) -> str:
        return str(self.title)


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

    def __str__(self) -> str:
        return f"{self.fetch_date}: {self.status}"
