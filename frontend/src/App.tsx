import React from "react";
import { Routes, Route } from "react-router-dom";
import MainRoutes from "./router/main";
import AuthRoutes from "./router/auth";

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainRoutes />} />
      <Route path="/auth/*" element={<AuthRoutes />} />
    </Routes>
  );
}

export default App;
