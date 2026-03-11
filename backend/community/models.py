from django.conf import settings
from django.db import models


class Community(models.Model):
    post_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    hit = models.PositiveIntegerField(default=0)
    is_image = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} (#{self.post_id})"


class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    post = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    com_comment = models.TextField()
    com_posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments",
    )

    class Meta:
        ordering = ["com_posted_at"]

    def __str__(self) -> str:
        return f"{self.user} on #{self.post.post_id}"
