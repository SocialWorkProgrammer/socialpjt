/**
 * Firebase 이메일 링크 인증 유틸리티 함수들
 *
 * 이 파일은 Firebase Authentication의 이메일 링크 인증 기능을 구현합니다.
 * 사용자가 이메일 주소만으로 비밀번호 없이 로그인할 수 있게 해줍니다.
 *
 * 참고 문서: https://firebase.google.com/docs/auth/web/email-link-auth
 */

import { sendSignInLinkToEmail } from "firebase/auth";
import { auth } from "../firebase";

/**
 * Firebase 이메일 링크 인증 설정 객체
 *
 * Firebase가 이메일 링크를 생성할 때 사용할 설정들을 정의합니다.
 * 이 설정들은 sendSignInLinkToEmail 함수에서 사용됩니다.
 */
const actionCodeSettings = {
  // 🔗 리디렉션 URL: 사용자가 이메일 링크를 클릭했을 때 돌아올 페이지
  // 주의: 이 도메인은 Firebase 콘솔의 승인된 도메인 목록에 있어야 합니다!
  url: "https://www.example.com/finishSignUp?cartId=1234", // 실제 배포시에는 실제 도메인으로 변경 필요

  // 📱 앱에서 링크 처리: 모바일 앱에서도 링크를 처리할 수 있도록 설정
  // 반드시 true로 설정해야 합니다!
  handleCodeInApp: true,

  // 🍎 iOS 앱 설정 (선택사항)
  // iOS 앱이 있다면 Bundle ID를 설정하여 앱에서 직접 링크를 처리할 수 있습니다
  iOS: {
    bundleId: "com.example.ios", // 실제 iOS 번들 ID로 변경
  },

  // 🤖 Android 앱 설정 (선택사항)
  // Android 앱이 있다면 패키지명을 설정하여 앱에서 직접 링크를 처리할 수 있습니다
  android: {
    packageName: "com.example.android", // 실제 Android 패키지명으로 변경
    installApp: true, // 앱이 설치되지 않은 경우 Play Store로 리디렉션
    minimumVersion: "12", // 최소 지원 버전
  },

  // 🌐 커스텀 도메인 (선택사항)
  // Firebase Hosting에서 설정한 커스텀 도메인을 사용할 때 설정
  linkDomain: "custom-domain.com", // 실제 커스텀 도메인으로 변경
};

/**
 * 사용자의 이메일로 로그인 링크를 전송하는 함수
 *
 * 이 함수는 Login 컴포넌트에서 호출되어 실제로 Firebase에게
 * 지정된 이메일 주소로 로그인 링크를 보내달라고 요청합니다.
 *
 * @param email - 로그인 링크를 받을 사용자의 이메일 주소
 * @returns Promise<void> - 비동기 함수이므로 await 또는 .then()으로 처리
 *
 * @example
 * // Login.tsx에서 사용 예시
 * const handleSubmit = async (e) => {
 *   try {
 *     await sendLoginLink(userEmail);
 *     alert('이메일을 확인해주세요!');
 *   } catch (error) {
 *     alert('이메일 전송 실패: ' + error.message);
 *   }
 * };
 */
export const sendLoginLink = async (email: string) => {
  try {
    // 🚀 Firebase Authentication API를 호출하여 이메일 링크 전송
    await sendSignInLinkToEmail(auth, email, actionCodeSettings);

    // ✅ 성공시 로그 출력 (실제 서비스에서는 제거하거나 적절한 로깅 시스템 사용)
    console.log(`이메일 링크가 ${email}로 성공적으로 전송되었습니다.`);

    // 💾 이메일 주소를 로컬 스토리지에 저장
    // 나중에 사용자가 링크를 클릭했을 때 이메일을 다시 입력하지 않아도 되도록 저장
    window.localStorage.setItem("emailForSignIn", email);
  } catch (error) {
    // ❌ 에러 발생시 콘솔에 출력하고 상위로 에러를 전파
    console.error("이메일 링크 전송 실패:", error);
    throw error; // 호출하는 쪽에서 에러를 처리할 수 있도록 다시 throw
  }
};

// 📤 다른 파일에서 사용할 수 있도록 export
// actionCodeSettings는 다른 곳에서 참조할 일이 있을 수 있으므로 export
export { actionCodeSettings };
