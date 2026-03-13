import { Navigate, Route, Routes } from "react-router-dom";

import MainPage from "../pages/main/Main.tsx";
import SiteShell from "../components/SiteShell.tsx";
import { ServiceRecommendPage, ServiceDetailPage, ServiceListPage } from "../pages/services/ServicePages";
import { NewsDetailPage, NewsListPage } from "../pages/news/NewsPages.tsx";
import { CommunityDetailPage, CommunityListPage } from "../pages/community/CommunityPages.tsx";

const MainRoutes = () => {
  return (
    <SiteShell>
      <Routes>
        <Route index element={<MainPage />} />
        <Route path="services" element={<ServiceListPage />} />
        <Route path="services/recommend" element={<ServiceRecommendPage />} />
        <Route path="services/:serviceId" element={<ServiceDetailPage />} />
        <Route path="news" element={<NewsListPage />} />
        <Route path="news/:newsId" element={<NewsDetailPage />} />
        <Route path="community" element={<CommunityListPage />} />
        <Route path="community/:postId" element={<CommunityDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </SiteShell>
  );
};

export default MainRoutes;
