import { useAuthStore } from '../../store/authStore';
import { useLayoutStore } from '../../store/layoutStore';

export function MobileNavBar() {
  const { user } = useAuthStore();
  const { toggleMobileMenu } = useLayoutStore();
  
  return (
    <header className="md:hidden flex items-center justify-between px-6 py-4 fixed top-0 w-full z-40 bg-white/70 backdrop-blur-xl shadow-sm border-b border-zinc-100">
      <div className="flex items-center gap-3">
        <button onClick={toggleMobileMenu} className="flex items-center justify-center p-1 -ml-1 rounded-md hover:bg-zinc-100 transition-colors">
          <span className="material-symbols-outlined text-[var(--color-primary)]">menu</span>
        </button>
        <h1 className="font-headline text-lg font-semibold tracking-tight text-green-900">관찰 일지 작성</h1>
      </div>
      <div className="w-8 h-8 rounded-full bg-[var(--color-surface-container)] overflow-hidden">
        <img 
          className="w-full h-full object-cover" 
          alt="Professional portrait" 
          src={user?.email === 'user@example.com' ? "https://lh3.googleusercontent.com/aida-public/AB6AXuAUu-UvnXOZ2h4Yn67oztWuXr0wM-xtW9BUx39JfM970ZsFMNysq6KoE2tF1NgDJ8zioB43aS8Sz_1fwSHp_Qz41iWzlKM-n4IeHG9ULU8URNndx8Ed55zggbUa3MmlHofumoAl5w_1Jh2RfLou8-iSnvN0F7eXFMaEsGS8kfbn1kYTLYLOFcRmX8350DR32H_XoJHjolWsr_SQYlPqGzM9R0wfc3rPO3pNsiAzmEjfcrklksdDnZXc5RwkIlT2rIIJVKKAT1yoFw" : "https://lh3.googleusercontent.com/aida-public/AB6AXuDS50v-bDzSBnsD_Gk03h8AdlKkIL5blfFkaQM8sTQCpjtFG76R05j5PyBbAdpO5BerkfxKQc8-nWR_HwCzx4oij98fFmya331jHY7uLDrzSfEn1n8Pw8sJmgKH_MkWawcEoRbmPfoZeQKp-IrIC3oZWkh42jM9laLcYDK47FbYtDjZUWUYcEm6kd6K-eNNRQNbZtryPFZ7iWQbxHkA5oh7_OkYPRVg1M6r5SlCU4-MfZAR-m-9dDRL25T8_NbSI14zm8iJ9ru2Pw"} 
        />
      </div>
    </header>
  );
}
