from django.db import models


class SocialService(models.Model):
    SOURCE_NATIONAL = "national"
    SOURCE_LOCAL = "local"
    SOURCE_ODCLOUD = "odcloud"
    SOURCE_CHOICES = [
        (SOURCE_NATIONAL, "중앙부처복지서비스"),
        (SOURCE_LOCAL, "지자체복지서비스"),
        (SOURCE_ODCLOUD, "복지서비스정보"),
    ]

    social_service_id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    detail_url = models.URLField(blank=True)
    site_url = models.URLField(blank=True)
    contact = models.CharField(max_length=255, blank=True)
    ministry = models.CharField(max_length=120, blank=True)
    organization = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    base_year = models.PositiveIntegerField(null=True, blank=True)
    region_ctpv = models.CharField(max_length=50, blank=True)
    region_sgg = models.CharField(max_length=50, blank=True)
    support_cycle = models.CharField(max_length=80, blank=True)
    support_type = models.CharField(max_length=120, blank=True)
    apply_method_name = models.CharField(max_length=120, blank=True)
    apply_method_detail = models.TextField(blank=True)
    target_detail = models.TextField(blank=True)
    selection_criteria = models.TextField(blank=True)
    benefit_detail = models.TextField(blank=True)
    welfare_outline = models.TextField(blank=True)
    online_applicable = models.BooleanField(null=True, blank=True)
    view_count = models.PositiveIntegerField(null=True, blank=True)
    first_registered_at = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    last_modified = models.DateField(null=True, blank=True)

    # 중앙부처 lifeArray: 001 영유아, 002 아동, 003 청소년, 004 청년, 005 중장년, 006 노년, 007 임신 출산
    life_codes = models.CharField(max_length=200, blank=True)
    # 중앙부처 trgterIndvdlArray: 010 다문화 탈북민, 020 다자녀, 030 보훈대상자, 040 장애인, 050 저소득, 060 한부모 조손
    target_codes = models.CharField(max_length=200, blank=True)
    # 중앙부처 intrsThemaArray: 010 신체건강, 020 정신건강, 030 생활지원, 040 주거, 050 일자리, 060 문화 여가, 070 안전 위기, 080 임신 출산, 090 보육, 100 교육, 110 입양 위탁, 120 보호 돌봄, 130 서민금융, 140 법률
    theme_codes = models.CharField(max_length=200, blank=True)

    life_names = models.CharField(max_length=200, blank=True)
    target_names = models.CharField(max_length=200, blank=True)
    theme_names = models.CharField(max_length=200, blank=True)

    contact_list = models.JSONField(default=list, blank=True)
    homepage_list = models.JSONField(default=list, blank=True)
    law_list = models.JSONField(default=list, blank=True)
    form_list = models.JSONField(default=list, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering = ["-fetched_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="unique_social_service_source_external_id",
            )
        ]

    def __str__(self) -> str:
        return f"[{self.source}] {self.title}"


class ServiceFetchStatus(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILURE = "failure"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "성공"),
        (STATUS_FAILURE, "실패"),
    ]

    source = models.CharField(max_length=20, choices=SocialService.SOURCE_CHOICES)
    fetch_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "fetch_date"],
                name="unique_service_fetch_status_source_date",
            )
        ]
        ordering = ["-fetch_date", "source"]
        verbose_name = "사회서비스 수집 상태"
        verbose_name_plural = "사회서비스 수집 상태"

    def __str__(self) -> str:
        return f"{self.fetch_date} {self.source}: {self.status}"
