import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate("/");
    }
  }, [loading, isAuthenticated, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "로그인 요청이 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-shell">
      <form className="auth-card fade-in" onSubmit={handleSubmit}>
        <h1 className="text-2xl font-semibold">로그인</h1>

        <label className="form-field">
          <span>이메일</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span>비밀번호</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        {error && <p className="text-error">{error}</p>}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "처리 중..." : "로그인"}
        </button>

        <p className="helper-link">
          아직 회원이 아니신가요? <Link to="/auth/signup">회원가입</Link>
        </p>
      </form>
    </section>
  );
}

export default Login;
