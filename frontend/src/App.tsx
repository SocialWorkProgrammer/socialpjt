import { Route, Routes } from "react-router-dom";

import MainRoutes from "./router/main";
import AuthRoutes from "./router/auth";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/auth/*" element={<AuthRoutes />} />
      <Route
        path="*"
        element={
          <ProtectedRoute>
            <MainRoutes />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
