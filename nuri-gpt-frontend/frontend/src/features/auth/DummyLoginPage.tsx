import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export const DummyLoginPage = () => {
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = () => {
    login('dummy-access-token', { id: 'dummy-user', email: 'dummy@example.com' }); // 전역 상태 isAuthenticated를 true로 변경
    navigate('/observations'); // 메인 페이지로 리다이렉트
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <div className="p-8 bg-white rounded-lg shadow-md w-96 text-center">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">누리 GPT 로그인</h1>
        <p className="mb-6 text-gray-600">이 페이지는 임시 로그인 페이지입니다.</p>
        <button
          onClick={handleLogin}
          className="w-full bg-blue-600 text-white font-semibold py-2 px-4 rounded hover:bg-blue-700 transition duration-200"
        >
          더미 로그인 버튼 (접속)
        </button>
      </div>
    </div>
  );
};
