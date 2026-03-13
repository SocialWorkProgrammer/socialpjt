import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

type SiteShellProps = {
  children: ReactNode;
};

export default function SiteShell({ children }: SiteShellProps) {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <nav className="app-nav">
          <span className="brand">사회복지 연결고리</span>
          <NavLink to="/" end>
            {({ isActive }) => <span className={isActive ? "active" : ""}>대시보드</span>}
          </NavLink>
          <NavLink to="/services">
            {({ isActive }) => <span className={isActive ? "active" : ""}>서비스</span>}
          </NavLink>
          <NavLink to="/services/recommend">
            {({ isActive }) => (
              <span className={isActive ? "active" : ""}>AI 추천</span>
            )}
          </NavLink>
          <NavLink to="/news">
            {({ isActive }) => <span className={isActive ? "active" : ""}>뉴스</span>}
          </NavLink>
          <NavLink to="/community">
            {({ isActive }) => <span className={isActive ? "active" : ""}>커뮤니티</span>}
          </NavLink>
        </nav>
        <div className="user-area">
          <span>{user?.email}</span>
          <button
            type="button"
            onClick={() => void logout()}
            className="ghost-button"
          >
            로그아웃
          </button>
        </div>
      </header>
      <main className="page-shell">{children}</main>
    </div>
  );
}
