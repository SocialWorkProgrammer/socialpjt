# Node.js 기반 이미지 사용
FROM node:20

# 작업 디렉토리 생성
WORKDIR /app

# 종속성 설치용 파일 복사 (캐시 레이어 최적화)
COPY package*.json ./

# 의존성 설치
RUN npm install

# 앱 소스 복사
COPY . .

# Vite 개발 서버 포트
EXPOSE 5173

# 컨테이너 시작 시 Vite dev 서버 실행
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]