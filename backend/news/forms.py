from django import forms

from .models import NewsComment


class NewsCommentForm(forms.ModelForm):
    class Meta:
        model = NewsComment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 3, "placeholder": "의견을 입력하세요"}
            )
        }
