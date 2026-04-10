import { CircleHelp } from 'lucide-react';
import { LoginForm } from '../components/LoginForm';

export const LoginPage = () => {
  return (
    <div className="min-h-screen bg-[var(--color-surface)] text-[var(--color-on-surface)] flex flex-col">
      <header className="fixed top-0 w-full z-50 bg-white/70 backdrop-blur-[12px]">
        <div className="flex justify-between items-center px-6 py-5 w-full max-w-7xl mx-auto">
          <div className="text-xl font-headline font-bold text-[var(--color-primary)] italic tracking-tight">
            Nuri-GPT
          </div>
          <button className="text-[var(--color-on-surface-variant)] font-body text-sm hover:text-[var(--color-primary)] transition-colors flex items-center gap-1">
            <CircleHelp className="w-5 h-5" />
            지원
          </button>
        </div>
      </header>

      <main className="flex-grow flex items-center justify-center px-6 pt-24 pb-12 relative overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(195,239,173,0.15)_0%,transparent_40%),radial-gradient(circle_at_bottom_right,rgba(195,239,173,0.1)_0%,transparent_40%)]">
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-[var(--color-primary-container)]/20 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-[var(--color-secondary-container)]/20 rounded-full blur-[100px]" />

        <div className="w-full max-w-[440px] z-10">
          <LoginForm />
          <p className="text-center mt-8 font-body text-sm text-[var(--color-on-surface-variant)]">
            Nuri-GPT가 처음이신가요?{' '}
            <a className="text-[var(--color-primary)] font-bold hover:underline decoration-2 underline-offset-4" href="#">
              계정 만들기
            </a>
          </p>
        </div>
      </main>

      <footer className="w-full py-8 bg-[var(--color-surface-container-low)]">
        <div className="flex flex-col md:flex-row justify-between items-center px-8 gap-4 w-full max-w-7xl mx-auto">
          <div className="font-body text-xs text-[var(--color-on-surface-variant)]">© 2024 Nuri-GPT. The Digital Curator.</div>
          <div className="flex gap-6">
            <a className="font-body text-xs text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)] transition-colors duration-200" href="#">
              개인정보처리방침
            </a>
            <a className="font-body text-xs text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)] transition-colors duration-200" href="#">
              서비스 이용약관
            </a>
            <a className="font-body text-xs text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)] transition-colors duration-200" href="#">
              지원
            </a>
            <a className="font-body text-xs text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)] transition-colors duration-200" href="#">
              문의
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
