import { Link } from "react-router-dom";

const Main = () => {
  return (
    <section className="panel fade-in">
      <h1 className="heading">사회복지 연결고리</h1>
      <p className="mt-2">로그인 후 맞춤 서비스 조회, 뉴스, 커뮤니티를 한 화면에서 이용하세요.</p>

      <div className="card-grid mt-4">
        <Link to="/services" className="result-card">
          <h2 className="text-lg font-semibold">서비스</h2>
          <p>복지 서비스 검색과 상세 정보를 확인하세요.</p>
        </Link>

        <Link to="/services/recommend" className="result-card">
          <h2 className="text-lg font-semibold">AI 추천</h2>
          <p>사용자 정보를 입력해 추천 목록을 받아보세요.</p>
        </Link>

        <Link to="/news" className="result-card">
          <h2 className="text-lg font-semibold">뉴스</h2>
          <p>복지 관련 공지와 정책 소식을 확인하세요.</p>
        </Link>

        <Link to="/community" className="result-card">
          <h2 className="text-lg font-semibold">커뮤니티</h2>
          <p>경험 공유와 질문 게시판으로 소통하세요.</p>
        </Link>
      </div>
    </section>
  );
};

export default Main;
