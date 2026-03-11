from django import forms

from .models import Comment, Community


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["title", "description", "is_image"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "제목을 입력하세요"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["com_comment"]
        widgets = {
            "com_comment": forms.Textarea(
                attrs={"rows": 3, "placeholder": "댓글을 입력하세요"}
            )
        }
