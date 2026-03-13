import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../types/http";
import {
  getCommunityDetail,
  getCommunityList,
  type CommunityItem,
} from "../../api/community";

type CommunityState = {
  items: CommunityItem[];
  pagination: {
    has_previous: boolean;
    has_next: boolean;
    page: number;
    total_pages: number;
  };
};

function CommunityEmptyState() {
  return (
    <section className="panel fade-in">
      <h2>게시글이 없습니다.</h2>
      <p>작성된 글이 없다면 처음으로 글을 추가해 보세요.</p>
    </section>
  );
}

export function CommunityListPage() {
  const [query, setQuery] = useState("");
  const [draftQuery, setDraftQuery] = useState("");
  const [state, setState] = useState<CommunityState>({
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

    getCommunityList({ q: query, page: state.pagination.page })
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
      <h1 className="heading">커뮤니티</h1>

      <form className="search-row" onSubmit={handleSearch}>
        <input
          value={draftQuery}
          onChange={(event) => setDraftQuery(event.target.value)}
          placeholder="게시글 제목 검색"
        />
        <button type="submit" className="ghost-button">
          검색
        </button>
      </form>

      {isLoading ? <p>불러오는 중...</p> : null}
      {error ? <p className="text-error">{error}</p> : null}

      {!isLoading && state.items.length === 0 ? <CommunityEmptyState /> : null}

      {state.items.length > 0 ? (
        <>
          <ul className="news-list">
            {state.items.map((post) => (
              <li key={post.id} className={`result-card ${post.is_pinned ? "is-pinned" : ""}`}>
                <Link to={`/community/${post.id}`}>
                  {post.title}
                  {post.is_pinned ? " [고정]" : ""}
                </Link>
                <p className="meta">
                  {post.author_email || "익명"} · 조회수 {post.view_count} · {new Date(post.created_at).toLocaleString()}
                </p>
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

export function CommunityDetailPage() {
  const { postId } = useParams<{ postId: string }>();
  const navigate = useNavigate();
  const [item, setItem] = useState<CommunityItem | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!postId) {
      return;
    }

    getCommunityDetail(postId)
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
  }, [postId, navigate]);

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
        {item.author_email || "익명"} · 조회수 {item.view_count} · {new Date(item.created_at).toLocaleString()}
      </p>
      <pre className="whitespace-pre-wrap">{item.content}</pre>
    </article>
  );
}
