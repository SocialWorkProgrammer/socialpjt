import React from "react";
import { Route, Routes } from "react-router-dom";

import MainPage from "../pages/main/Main.tsx";

const MainRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      {/* 향후 추가될 메인 페이지 관련 라우트들 */}
      {/* <Route path="/profile" element={<Profile />} /> */}
      {/* <Route path="/community" element={<Community />} /> */}
      {/* <Route path="/dashboard" element={<Dashboard />} /> */}
    </Routes>
  );
};

export default MainRoutes;
