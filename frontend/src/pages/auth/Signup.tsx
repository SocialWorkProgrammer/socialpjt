import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

function Signup() {
  const navigate = useNavigate();
  const { signup, isAuthenticated, loading } = useAuth();

  const [email, setEmail] = useState("");
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
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
      await signup({ email, password1, password2 });
      navigate("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "회원가입 요청이 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-shell">
      <form className="auth-card fade-in" onSubmit={handleSubmit}>
        <h1 className="text-2xl font-semibold">회원가입</h1>

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
            value={password1}
            onChange={(event) => setPassword1(event.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span>비밀번호 확인</span>
          <input
            type="password"
            value={password2}
            onChange={(event) => setPassword2(event.target.value)}
            required
          />
        </label>

        {error && <p className="text-error">{error}</p>}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "처리 중..." : "계정 만들기"}
        </button>

        <p className="helper-link">
          이미 계정이 있으면 <Link to="/auth/login">로그인</Link>
        </p>
      </form>
    </section>
  );
}

export default Signup;
