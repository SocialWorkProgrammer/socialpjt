import React from "react";
import { Route, Routes } from "react-router-dom";

import Login from "../pages/auth/Login";

const AuthRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {/* 향후 추가될 인증 관련 라우트들 */}
      {/* <Route path="/register" element={<Register />} /> */}
      {/* <Route path="/forgot-password" element={<ForgotPassword />} /> */}
    </Routes>
  );
};

export default AuthRoutes;
