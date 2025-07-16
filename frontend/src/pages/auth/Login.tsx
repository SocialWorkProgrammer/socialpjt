import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import "../../router/App.css";

const DUMMY_USER = {
  email: "test@example.com",
  password: "1234",
};

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setError("");
      if (email === DUMMY_USER.email && password === DUMMY_USER.password) {
        // 로그인 성공 시 메인 페이지로 이동 ("/" 경로 예시)
        navigate("/");
      } else {
        setError("이메일 또는 비밀번호가 올바르지 않습니다.");
      }
    },
    [email, password, navigate]
  );

  return (
    <div className="w-full min-w-screen min-h-screen flex items-center justify-center py-8">
      <div className="flex flex-col md:flex-row bg-[#224bd3] rounded-2xl shadow-2xl w-full max-w-6xl overflow-hidden">
        <div className="hidden md:block md:w-1/2 bg-primary-600 p-12 relative">
          <div className="absolute top-0 left-0 w-full h-full bg-primary-700 opacity-20 z-10"></div>
          <div className="relative z-20 h-full flex flex-col justify-center">
            <h2 className="text-4xl font-bold text-white mb-6">
              Join our community today
            </h2>
            <p className="text-white text-lg mb-8 opacity-90">
              Access exclusive resources, connect with like-minded individuals,
              and take your experience to the next level.
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

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                  lock
                </span>
                <input
                  type="password"
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 outline-none"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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
              className="w-full bg-primary-500 text-white py-3 rounded-lg font-semibold hover:bg-primary-600 transform transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
            >
              Sign In
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
