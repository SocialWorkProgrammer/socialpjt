import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../types/http";
import { getNewsDetail, getNewsList, type NewsItem } from "../../api/news";

type NewsListState = {
  items: NewsItem[];
  pagination: {
    has_previous: boolean;
    has_next: boolean;
    page: number;
    total_pages: number;
  };
};

function NewsEmptyState() {
  return (
    <section className="panel fade-in">
      <h2>뉴스가 없습니다.</h2>
      <p>새 공지나 기사 데이터가 등록되면 이곳에 표시됩니다.</p>
    </section>
  );
}

export function NewsListPage() {
  const [query, setQuery] = useState("");
  const [draftQuery, setDraftQuery] = useState("");
  const [state, setState] = useState<NewsListState>({
    items: [],
    pagination: {
      has_previous: false,
      has_next: false,
      page: 1,
      total_pages: 1,
    },
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError("");

    getNewsList({ q: query, page: state.pagination.page })
      .then((response) => {
        if (!active) {
          return;
        }
        setState({
          items: response.items,
          pagination: {
            has_previous: response.pagination.has_previous,
            has_next: response.pagination.has_next,
            page: response.pagination.page,
            total_pages: response.pagination.total_pages,
          },
        });
      })
      .catch((err: unknown) => {
        if (!active) {
          return;
        }
        if (err instanceof ApiError && err.status === 401) {
          navigate("/auth/login", { replace: true });
          return;
        }
        setError(err instanceof Error ? err.message : "목록을 불러오지 못했습니다.");
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [query, state.pagination.page, navigate]);

  const updatePage = (next: number) => {
    setState((prev) => ({
      ...prev,
      pagination: {
        ...prev.pagination,
        page: next,
      },
    }));
  };

  const handleSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setState((prev) => ({
      ...prev,
      pagination: {
        ...prev.pagination,
        page: 1,
      },
    }));
    setQuery(draftQuery);
  };

  return (
    <section className="panel fade-in">
      <h1 className="heading">뉴스</h1>

      <form className="search-row" onSubmit={handleSearch}>
        <input
          value={draftQuery}
          onChange={(event) => setDraftQuery(event.target.value)}
          placeholder="뉴스 제목 검색"
        />
        <button type="submit" className="ghost-button">
          검색
        </button>
      </form>

      {isLoading ? <p>불러오는 중...</p> : null}
      {error ? <p className="text-error">{error}</p> : null}

      {!isLoading && state.items.length === 0 ? <NewsEmptyState /> : null}

      {state.items.length > 0 ? (
        <>
          <ul className="news-list">
            {state.items.map((news) => (
              <li key={news.news_id} className="result-card">
                <Link to={`/news/${news.news_id}`}>{news.title}</Link>
                <p className="meta">{new Date(news.created_at).toLocaleString()} · {news.source_url}</p>
              </li>
            ))}
          </ul>

          <div className="pagination-row">
            <button
              type="button"
              disabled={!state.pagination.has_previous}
              onClick={() => updatePage(state.pagination.page - 1)}
            >
              이전
            </button>
            <span>
              {state.pagination.page} / {state.pagination.total_pages}
            </span>
            <button
              type="button"
              disabled={!state.pagination.has_next}
              onClick={() => updatePage(state.pagination.page + 1)}
            >
              다음
            </button>
          </div>
        </>
      ) : null}
    </section>
  );
}

export function NewsDetailPage() {
  const { newsId } = useParams<{ newsId: string }>();
  const navigate = useNavigate();
  const [item, setItem] = useState<NewsItem | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!newsId) {
      return;
    }

    getNewsDetail(newsId)
      .then((response) => {
        setItem(response.item);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          navigate("/auth/login", { replace: true });
          return;
        }
        setError(err instanceof Error ? err.message : "상세 정보를 불러오지 못했습니다.");
      });
  }, [newsId, navigate]);

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
      <p className="meta">
        {new Date(item.created_at).toLocaleString()} · {item.source_url}
      </p>
      <pre className="whitespace-pre-wrap">{item.content}</pre>
      {item.source_url ? (
        <a className="mt-2 inline-block text-blue-600" href={item.source_url} target="_blank" rel="noreferrer">
          원문 보러가기
        </a>
      ) : null}
    </article>
  );
}
