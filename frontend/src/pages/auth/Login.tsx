import React, { useState, useCallback } from "react";
// import { useNavigate } from "react-router-dom";
import { sendLoginLink } from "../../utils/emailAuth";
import "../../main.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState("");
  // const navigate = useNavigate();

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
      } catch (error: unknown) {
        setError(`${email}에 대한 전송이 실패했습니다.${error}`);
      } finally {
        setLoading(false);
      }
    },
    // 의존성 배열: 이 값들이 변경될 때만 함수 재생성
    // - email, password: 사용자 입력값
    // - navigate: React Router 함수 (보통 변경되지 않음)
    [email]
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
              <span className="material-symbols-outlined text-white text-2xl">
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
              <label className="text-sm font-medium text-gray-700">
                Email Address
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                  mail
                </span>
                <input
                  type="email"
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 outline-none"
                  placeholder="Enter your email"
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
                  className="w-4 h-4 text-primary-500 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-600">Remember me</span>
              </label>
              <a
                href="#"
                className="text-sm text-primary-500 hover:text-primary-600 transition-colors duration-200"
              >
                Forgot password?
              </a>
            </div>

            {error && (
              <div className="text-red-500 text-sm text-center">{error}</div>
            )}

            <button
              type="submit"
              disabled={loading || emailSent}
              className="w-full bg-primary-500 text-white py-3 rounded-lg font-semibold hover:bg-primary-600 transform transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
            >
              {emailSent
                ? "이메일 전송 완료"
                : loading
                ? "이메일 전송 중.."
                : "로그인"}
            </button>
          </form>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Or continue with
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-3">
              <button className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-center hover:bg-gray-50 transition-colors duration-200 hover:scale-105 transform shadow-sm">
                <i className="fab fa-google text-red-500 text-xl"></i>
              </button>
              <button className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-center hover:bg-gray-50 transition-colors duration-200 hover:scale-105 transform shadow-sm">
                <i className="fab fa-facebook text-blue-600 text-xl"></i>
              </button>
              <button className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-center hover:bg-gray-50 transition-colors duration-200 hover:scale-105 transform shadow-sm">
                <i className="fab fa-twitter text-blue-400 text-xl"></i>
              </button>
            </div>
          </div>

          <div className="mt-8 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?
              <a
                href="#"
                className="text-primary-500 hover:text-primary-600 font-semibold ml-1 transition-colors duration-200"
              >
                Sign up
              </a>
            </p>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-100">
            <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
              <span className="material-symbols-outlined text-sm">shield</span>
              <span>Secure login protected by SSL encryption</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
