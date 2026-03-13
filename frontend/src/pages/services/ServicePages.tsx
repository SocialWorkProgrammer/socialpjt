import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../types/http";
import {
  getRecommendation,
  getService,
  getServices,
  type RecommendationPayload,
  type SocialServiceItem,
} from "../../api/services";

function EmptyState() {
  return (
    <section className="panel fade-in">
      <h2>표시할 데이터가 없습니다.</h2>
      <p>현재 데이터가 없다면 관리자 페이지에서 수집 작업이 필요합니다.</p>
    </section>
  );
}

export function ServiceListPage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<SocialServiceItem[]>([]);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<{
    has_previous: boolean;
    has_next: boolean;
    page: number;
    total_pages: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setError("");

    getServices({ q: query, page })
      .then((response) => {
        if (!isMounted) {
          return;
        }
        if (response.ok) {
          setItems(response.items);
          setPagination(response.pagination);
        }
      })
      .catch((err: unknown) => {
        if (!isMounted) {
          return;
        }
        if (err instanceof ApiError && err.status === 401) {
          navigate("/auth/login", { replace: true });
          return;
        }
        setError(err instanceof Error ? err.message : "목록을 불러오지 못했습니다.");
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [query, page, navigate]);

  return (
    <section className="panel fade-in">
      <h1 className="heading">사회서비스</h1>
      <div className="search-row">
        <input
          value={query}
          onChange={(event) => {
            setPage(1);
            setQuery(event.target.value);
          }}
          placeholder="서비스명을 검색하세요"
        />
      </div>

      {isLoading ? <p>불러오는 중...</p> : null}
      {error ? <p className="text-error">{error}</p> : null}

      {!isLoading && items.length === 0 ? <EmptyState /> : null}

      {items.length > 0 && (
        <>
          <div className="card-grid">
            {items.map((service) => (
              <Link key={service.id} className="result-card" to={`/services/${service.id}`}>
                <h3>{service.title}</h3>
                <p>{service.summary || "요약 정보가 없습니다."}</p>
                <p className="meta">
                  {service.source_label}
                  {service.region_ctpv ? ` · ${service.region_ctpv}` : ""}
                </p>
              </Link>
            ))}
          </div>

          {pagination ? (
            <div className="pagination-row">
              <button type="button" disabled={!pagination.has_previous} onClick={() => setPage(page - 1)}>
                이전
              </button>
              <span>
                {pagination.page} / {pagination.total_pages}
              </span>
              <button type="button" disabled={!pagination.has_next} onClick={() => setPage(page + 1)}>
                다음
              </button>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}

export function ServiceDetailPage() {
  const { serviceId } = useParams<{ serviceId: string }>();
  const navigate = useNavigate();
  const [item, setItem] = useState<SocialServiceItem | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!serviceId) {
      return;
    }

    getService(serviceId)
      .then((response) => {
        if (response.ok) {
          setItem(response.item);
        }
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          navigate("/auth/login", { replace: true });
          return;
        }
        setError(err instanceof Error ? err.message : "상세 정보를 불러오지 못했습니다.");
      });
  }, [serviceId, navigate]);

  if (!item && !error) {
    return <section className="panel fade-in">상세 정보를 불러오는 중입니다.</section>;
  }

  if (error) {
    return <section className="panel fade-in text-error">{error}</section>;
  }

  if (!item) {
    return null;
  }

  return (
    <article className="panel fade-in">
      <h1 className="heading">{item.title}</h1>
      <p className="meta">{item.source_label}</p>
      <p>{item.summary}</p>
      <p>
        지역: {item.region_ctpv} {item.region_sgg}
      </p>
      <p>대상: {item.target_names || "-"}</p>
      <p>주요테마: {item.theme_names || "-"}</p>
      <p>신청방법: {item.apply_method_name || "-"}</p>
      {item.detail_url ? <a href={item.detail_url}>원문 페이지 바로가기</a> : null}
    </article>
  );
}

export function ServiceRecommendPage() {
  const navigate = useNavigate();

  const defaultForm: RecommendationPayload = {
    age_group: "",
    region_ctpv: "",
    region_sgg: "",
    target_type: "",
    life_stage: "",
    interest_theme: "",
    special_notes: "",
  };

  const [formState, setFormState] = useState(defaultForm);
  const [result, setResult] = useState<null | Awaited<ReturnType<typeof getRecommendation>>>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await getRecommendation(formState);
      setResult(response);
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        navigate("/auth/login", { replace: true });
        return;
      }
      setError(err instanceof Error ? err.message : "추천을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const setField = (key: keyof RecommendationPayload, value: string) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <section className="panel fade-in">
      <h1 className="heading">AI 추천 도우미</h1>

      <form className="search-row" onSubmit={handleSubmit}>
        <input
          placeholder="연령대"
          value={formState.age_group}
          onChange={(event) => setField("age_group", event.target.value)}
        />
        <input
          placeholder="시도"
          value={formState.region_ctpv}
          onChange={(event) => setField("region_ctpv", event.target.value)}
        />
        <input
          placeholder="시군구"
          value={formState.region_sgg}
          onChange={(event) => setField("region_sgg", event.target.value)}
        />
        <input
          placeholder="대상유형"
          value={formState.target_type}
          onChange={(event) => setField("target_type", event.target.value)}
        />
        <input
          placeholder="생애주기"
          value={formState.life_stage}
          onChange={(event) => setField("life_stage", event.target.value)}
        />
        <input
          placeholder="관심주제"
          value={formState.interest_theme}
          onChange={(event) => setField("interest_theme", event.target.value)}
        />
        <textarea
          placeholder="상담메모(민감정보 제외)"
          value={formState.special_notes}
          onChange={(event) => setField("special_notes", event.target.value)}
        />
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "생성 중..." : "추천받기"}
        </button>
      </form>

      {error && <p className="text-error">{error}</p>}

      {result ? (
        <article className="result-box">
          {result.llm.message && <p className="mb-2">{result.llm.message}</p>}

          <p className="muted">추천 후보</p>
          <ul>
            {result.recommendations.length === 0 ? (
              <li>조건에 맞는 서비스가 없습니다.</li>
            ) : (
              result.recommendations.map((item) => (
                <li key={`${item.service_id}-${item.title}`}>
                  {item.title}
                  <span className="muted"> · {item.region || "-"}</span>
                  <Link to={`/services/${item.service_id}`}>자세히 보기</Link>
                </li>
              ))
            )}
          </ul>

          <p className="mt-4 muted">{result.disclaimer}</p>
        </article>
      ) : null}
    </section>
  );
}
