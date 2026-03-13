from django.db import models


class CommunityPost(models.Model):
    """커뮤니티 게시글 엔티티.

    최소 동작 가능한 형태로 시작하고, 추후 댓글/좋아요는 별도 모델로 확장한다.
    """

    title = models.CharField(max_length=200)
    content = models.TextField()
    author_email = models.EmailField(blank=True)
    is_pinned = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self) -> str:
        return self.title
