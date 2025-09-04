import React, { useState, useCallback, useEffect } from "react";
// import { useNavigate } from "react-router-dom";
import { sendLoginLink } from "../../utils/emailAuth";
import "../../main.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  // const navigate = useNavigate();

  // 로컬 스토리지 키
  const REMEMBER_EMAIL_KEY = "remembered_email";

  // 컴포넌트 마운트 시 저장된 이메일 불러오기
  useEffect(() => {
    const savedEmail = localStorage.getItem(REMEMBER_EMAIL_KEY);
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  /**
   * 폼 제출 처리 함수 - 로그인 로직을 담당
   *
   * useCallback으로 감싸는 이유:
   * - 함수 메모이제이션으로 불필요한 리렌더링 방지
   * - 의존성 배열([email, password, navigate])의 값이 변경될 때만 함수 재생성
   * - 성능 최적화 + 자식 컴포넌트에 props 전달 시 안정성 보장
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      // 이벤트 객체 확인용 (개발자 도구 Console에서 확인 가능)
      // 1. 폼의 기본 제출 동작 방지 (페이지 새로고침 방지)
      e.preventDefault();
      setError("");
      setLoading(true);
      try {
        await sendLoginLink(email);
        setEmailSent(true);

        // Remember me 체크 상태에 따라 이메일 저장 또는 삭제
        if (rememberMe) {
          localStorage.setItem(REMEMBER_EMAIL_KEY, email);
        } else {
          localStorage.removeItem(REMEMBER_EMAIL_KEY);
        }
      } catch (error: unknown) {
        setError(`${email}에 대한 전송이 실패했습니다.${error}`);
      } finally {
        setLoading(false);
      }
    },
    // 의존성 배열: 이 값들이 변경될 때만 함수 재생성
    // - email: 사용자 입력값
    // - rememberMe: Remember me 체크박스 상태
    [email, rememberMe]
  );

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col md:flex-row rounded-2xl shadow-2xl max-w-6xl">
        <div className="hidden md:block md:w-2/3 p-12 relative">
          <div className="bg-[#224db3] absolute top-0 left-0 w-full h-full"></div>
          <div className="relative z-20 h-full flex flex-col justify-center">
            <h2 className="text-4xl font-bold text-white mb-6">
              사회복지사만을 위한 공간
            </h2>
            <p className="text-white text-lg mb-8 opacity-90">
              IT와 사회복지의 결합
            </p>
            <div className="bg-white/10 p-6 rounded-xl backdrop-blur-sm">
              <div className="flex items-center mb-4">
                <span className="material-symbols-outlined text-white mr-3">
                  verified
                </span>
                <p className="text-white">Premium content access</p>
              </div>
              <div className="flex items-center mb-4">
                <span className="material-symbols-outlined text-white mr-3">
                  forum
                </span>
                <p className="text-white">Community discussions</p>
              </div>
              <div className="flex items-center">
                <span className="material-symbols-outlined text-white mr-3">
                  event
                </span>
                <p className="text-white">Exclusive events</p>
              </div>
            </div>
            {/* Next: "Add testimonials carousel" */}
          </div>
        </div>

        <div className="w-full md:w-1/2 p-8 md:p-12">
          <div className="text-center mb-8">
            <div className="bg-primary-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
              <span className="material-symbols-outlined text-blue-400 text-2xl">
                groups
              </span>
            </div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              Welcome Back
            </h1>
            <p className="text-gray-600">Join our community</p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <div className="relative">
                <input
                  type="email"
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 outline-none"
                  placeholder="이메일을 입력하세요"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 text-primary-500 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-600">Remember me</span>
              </label>
            </div>

            {error && (
              <div className="text-red-500 text-sm text-center">{error}</div>
            )}
            <button
              type="submit"
              disabled={loading || emailSent}
              className="w-full bg-primary-500 text-black py-3 rounded-lg font-semibold hover:bg-primary-600 transform transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
            >
              <p>로그인</p>
            </button>
          </form>
          <div className="mt-6 pt-6 border-t border-gray-100">
            <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
              <span>Secure login protected by firebase</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
