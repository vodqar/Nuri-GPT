import { useLoginForm } from '../hooks/useLoginForm';

export const LoginForm = () => {
  const {
    register,
    formState: { errors },
    handleSubmit,
    isLoading,
  } = useLoginForm();

  return (
    <div className="bg-[var(--color-surface-container-lowest)] rounded-[2rem] shadow-[0_12px_32px_rgba(45,52,50,0.06)] p-8 md:p-10">
      <div className="text-center mb-10">
        <h1 className="font-headline text-3xl font-extrabold text-[var(--color-on-surface)] tracking-tight mb-2">
          환영합니다, 선생님!
        </h1>
        <p className="font-body text-[var(--color-on-surface-variant)] text-sm">
          커리큘럼 워크스페이스에 접속하세요.
        </p>
      </div>

      <form className="space-y-6" onSubmit={handleSubmit} noValidate>
        {errors.root && (
          <div className="p-4 rounded-xl bg-[var(--color-error)]/10 text-[var(--color-error)] text-sm text-center mb-4">
            {errors.root.message}
          </div>
        )}

        <div>
          <label className="block font-headline text-sm font-semibold text-[var(--color-on-surface)] mb-2 ml-1" htmlFor="email">
            이메일 주소
          </label>
          <input
            id="email"
            type="email"
            placeholder="name@school.edu"
            className="w-full px-5 py-4 bg-[var(--color-surface-container-low)] border-none rounded-xl focus:ring-1 focus:ring-[var(--color-primary)] focus:bg-[var(--color-surface-container-lowest)] transition-all placeholder:text-[var(--color-outline)] text-[var(--color-on-surface)]"
            {...register('email')}
            disabled={isLoading}
          />
          {errors.email ? (
            <p className="mt-2 ml-1 text-sm text-[var(--color-error)]">{errors.email.message}</p>
          ) : null}
        </div>

        <div>
          <div className="flex justify-between items-center mb-2 ml-1">
            <label className="block font-headline text-sm font-semibold text-[var(--color-on-surface)]" htmlFor="password">
              비밀번호
            </label>
            <a className="text-xs font-medium text-[var(--color-primary)] hover:text-[var(--color-primary-dim)] transition-colors" href="#" tabIndex={-1}>
              비밀번호를 잊으셨나요?
            </a>
          </div>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            className="w-full px-5 py-4 bg-[var(--color-surface-container-low)] border-none rounded-xl focus:ring-1 focus:ring-[var(--color-primary)] focus:bg-[var(--color-surface-container-lowest)] transition-all placeholder:text-[var(--color-outline)] text-[var(--color-on-surface)]"
            {...register('password')}
            disabled={isLoading}
          />
          {errors.password ? (
            <p className="mt-2 ml-1 text-sm text-[var(--color-error)]">{errors.password.message}</p>
          ) : null}
        </div>

        <div className="flex items-center ml-1">
          <input
            id="remember"
            type="checkbox"
            className="w-5 h-5 rounded border-[var(--color-outline)] text-[var(--color-primary)] focus:ring-[var(--color-primary)] focus:ring-offset-0 bg-[var(--color-surface-container-low)] transition-all"
            {...register('remember')}
            disabled={isLoading}
          />
          <label className="ml-3 text-sm text-[var(--color-on-surface-variant)] font-medium cursor-pointer" htmlFor="remember">
            로그인 유지
          </label>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-4 bg-[var(--color-primary)] text-[var(--color-on-primary)] font-headline font-bold rounded-xl shadow-lg shadow-[var(--color-primary)]/10 hover:bg-[var(--color-primary-dim)] transition-all active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center gap-2"
        >
          {isLoading ? '로그인 중...' : '로그인'}
        </button>

        <p className="text-xs text-[var(--color-on-surface-variant)] text-center mt-4 leading-relaxed">
          본인 확인을 위해 아이디와 비밀번호를 수집하며,
          <br />
          <a href="#" className="text-[var(--color-primary)] hover:underline underline-offset-2">개인정보처리방침</a>
          에 따라 안전하게 관리됩니다.
        </p>
      </form>
    </div>
  );
};
