import { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useLayoutStore } from '../../store/layoutStore';
import { cn } from '../../utils/cn';
import { logout as logoutApi } from '../../services/api';

export function SideNavBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuthStore();
  const { isSidebarCollapsed, toggleSidebar, isMobileMenuOpen, closeMobileMenu } = useLayoutStore();
  
  const [expandedMenus, setExpandedMenus] = useState<string[]>(['observations']);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const settingsRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setIsSettingsOpen(false);
      }
      // 모바일 메뉴 열려있을 때 사이드바 외부 클릭 시 닫기
      if (isMobileMenuOpen && sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        closeMobileMenu();
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMobileMenuOpen, closeMobileMenu]);

  const toggleAccordion = (menuId: string) => {
    setExpandedMenus(prev => 
      prev.includes(menuId) ? prev.filter(id => id !== menuId) : [...prev, menuId]
    );
  };

  const handleLogout = async () => {
    try {
      await logoutApi();
    } catch {
      // 세션 만료 등 서버 오류여도 로컬 상태는 초기화
    } finally {
      logout();
      navigate('/login');
    }
  };

  const navItems: { id: string; label: string; path: string; icon: string }[] = [];

  const categories = [
    {
      id: 'observations',
      label: '관찰',
      icon: 'visibility',
      items: [
        { label: '새 관찰 일지', path: '/observations' },
        { label: '인삿말 생성', path: '/observations/greeting' },
        { label: '생성 기록', path: '/observations/history' },
      ]
    }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      <div 
        className={cn(
          "fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity duration-300 md:hidden",
          isMobileMenuOpen ? "opacity-100 visible" : "opacity-0 invisible"
        )}
        onClick={closeMobileMenu}
      />

      <aside 
        ref={sidebarRef}
        className={cn(
          "h-screen fixed left-0 top-0 z-50 bg-zinc-50 dark:bg-zinc-950 flex flex-col border-r border-zinc-200 dark:border-zinc-800 shadow-[0_12px_32px_rgba(45,52,50,0.06)] transition-all duration-300 ease-in-out",
          // 모바일은 기본적으로 화면 밖, 데스크탑은 지정된 너비 적용
          "w-[280px]",
          isSidebarCollapsed ? "md:w-20" : "md:w-64",
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Toggle Button for Desktop */}
        <button
          onClick={toggleSidebar}
          className="hidden md:flex absolute -right-3.5 top-8 w-7 h-7 bg-white border border-zinc-200 rounded-full items-center justify-center text-zinc-500 hover:text-zinc-900 shadow-sm transition-transform hover:scale-110 z-50"
        >
          <span className="material-symbols-outlined text-[18px]">
            {isSidebarCollapsed ? "chevron_right" : "chevron_left"}
          </span>
        </button>

        {/* Brand Section */}
        <div className="p-6 transition-all duration-300">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-[var(--color-primary)] rounded-xl flex items-center justify-center shrink-0 text-[var(--color-on-primary)]">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>auto_stories</span>
            </div>
            <div className={cn(
              "transition-all duration-300 overflow-hidden whitespace-nowrap",
              isSidebarCollapsed ? "w-0 opacity-0" : "w-auto opacity-100"
            )}>
              <h2 className="font-headline text-lg font-extrabold text-green-900 dark:text-green-100 leading-tight">디지털 큐레이터</h2>
              <p className="text-xs font-medium text-[var(--color-on-surface-variant)]/70 uppercase tracking-widest">교육자 포털</p>
            </div>
          </div>

        {/* Primary Navigation */}
        <nav className="space-y-1">
          {navItems.length > 0 && navItems.map((item) => (
            <Link
              key={item.id}
              to={item.path}
              title={isSidebarCollapsed ? item.label : undefined}
              onClick={isMobileMenuOpen ? closeMobileMenu : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl transition-all duration-200 font-manrope text-sm font-medium",
                "px-4 py-3",
                location.pathname === item.path 
                  ? "text-green-900 border-r-4 border-green-800 bg-green-50/50" 
                  : "text-zinc-600 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:scale-[1.02]"
              )}
            >
              <span className="material-symbols-outlined shrink-0">{item.icon}</span>
              <span className={cn(
                "transition-all duration-300 overflow-hidden whitespace-nowrap",
                isSidebarCollapsed ? "w-0 opacity-0" : "w-auto opacity-100"
              )}>{item.label}</span>
            </Link>
          ))}

          {categories.map((cat) => {
            const isExpanded = !isSidebarCollapsed && expandedMenus.includes(cat.id);
            return (
              <div key={cat.id} className="accordion-item relative group/accordion">
                <button
                  onClick={() => !isSidebarCollapsed && toggleAccordion(cat.id)}
                  title={isSidebarCollapsed ? cat.label : undefined}
                  className={cn(
                    "w-full flex items-center justify-between rounded-xl font-manrope text-sm transition-all duration-200",
                    "px-4 py-3",
                    isExpanded
                      ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-semibold"
                      : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900 font-medium"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-colors duration-200",
                      isExpanded
                        ? "bg-[var(--color-primary)] text-[var(--color-on-primary)]"
                        : "bg-[var(--color-surface-container)] text-[var(--color-on-surface-variant)]"
                    )}>
                      <span
                        className="material-symbols-outlined shrink-0"
                        style={{ fontVariationSettings: isExpanded ? "'FILL' 1" : "'FILL' 0" }}
                      >
                        {cat.icon}
                      </span>
                    </div>
                    <span className={cn(
                      "transition-all duration-300 overflow-hidden whitespace-nowrap",
                      isSidebarCollapsed ? "w-0 opacity-0" : "w-auto opacity-100"
                    )}>{cat.label}</span>
                  </div>
                  {!isSidebarCollapsed && (
                    <span className={cn("material-symbols-outlined text-xs arrow-rotate", isExpanded && "rotated")}>
                      keyboard_arrow_down
                    </span>
                  )}
                </button>
                
                {/* 툴팁 (접힌 상태에서 호버 시) */}
                {isSidebarCollapsed && (
                  <div className="absolute left-full ml-2 top-0 bg-white shadow-lg rounded-xl border border-zinc-100 py-2 w-48 opacity-0 invisible group-hover/accordion:opacity-100 group-hover/accordion:visible transition-all z-50">
                    <div className="px-4 py-2 text-xs font-bold text-zinc-400 uppercase tracking-wider border-b border-zinc-100 mb-1">{cat.label}</div>
                    {cat.items.map((item, idx) => (
                      <Link
                        key={idx}
                        to={item.path}
                        onClick={isMobileMenuOpen ? closeMobileMenu : undefined}
                        className="block px-4 py-2 text-sm text-zinc-600 hover:text-[var(--color-primary)] hover:bg-zinc-50"
                      >
                        {item.label}
                      </Link>
                    ))}
                  </div>
                )}

                <div aria-expanded={isExpanded} className="menu-content">
                  <div className="menu-inner pl-11 pr-2 space-y-1 py-2">
                    {cat.items.map((item, idx) => {
                      const isActive = location.pathname === item.path;
                      return (
                        <Link
                          key={idx}
                          to={item.path}
                          onClick={isMobileMenuOpen ? closeMobileMenu : undefined}
                          className={cn(
                            "block px-3 py-2 text-sm transition-all duration-200 rounded-lg",
                            isActive
                              ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-medium"
                              : "text-zinc-500 hover:text-[var(--color-primary)] hover:bg-[var(--color-surface-container-low)]"
                          )}
                        >
                          {item.label}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}
        </nav>
      </div>

      {/* Footer Navigation */}
      <div className="mt-auto space-y-2 border-t border-zinc-100 dark:border-zinc-900 transition-all duration-300 p-4">
        <div className="relative" ref={settingsRef}>
          {/* Settings Submenu (Accordion above button) */}
          <div aria-expanded={isSettingsOpen && !isSidebarCollapsed} className="menu-content overflow-hidden">
            <div className="menu-inner pl-11 py-1 space-y-1">
              <Link to="/settings/account" onClick={isMobileMenuOpen ? closeMobileMenu : undefined} className="block py-1.5 text-xs text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)]">계정</Link>
              <Link to="#" onClick={isMobileMenuOpen ? closeMobileMenu : undefined} className="block py-1.5 text-xs text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)]">환경설정</Link>
            </div>
          </div>

          <button 
            onClick={() => !isSidebarCollapsed && setIsSettingsOpen(!isSettingsOpen)}
            title={isSidebarCollapsed ? "설정" : undefined}
            className={cn(
              "w-full flex items-center rounded-xl transition-all font-manrope text-sm font-medium",
              "px-4 py-2.5 justify-between",
              isSettingsOpen && !isSidebarCollapsed ? "text-green-900 bg-green-50/50" : "text-zinc-600 hover:bg-zinc-100"
            )}
          >
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined shrink-0">settings</span>
              <span className={cn(
                "transition-all duration-300 overflow-hidden whitespace-nowrap",
                isSidebarCollapsed ? "w-0 opacity-0" : "w-auto opacity-100"
              )}>설정</span>
            </div>
            {!isSidebarCollapsed && (
              <span className={cn("material-symbols-outlined text-xs transition-transform", isSettingsOpen && "rotate-180")}>keyboard_arrow_up</span>
            )}
          </button>
        </div>

        {/* Profile Card */}
        <div 
          ref={profileRef}
          onClick={() => !isSidebarCollapsed && setIsProfileOpen(!isProfileOpen)}
          className={cn(
            "relative group cursor-pointer rounded-xl transition-all duration-300 ease-out",
            "p-3",
            isProfileOpen && !isSidebarCollapsed
              ? "bg-white shadow-xl -translate-y-1" 
              : "bg-[var(--color-surface-container-low)] hover:bg-white hover:shadow-xl md:hover:-translate-y-1"
          )}
        >
          <div className={cn("flex items-center", isSidebarCollapsed ? "justify-center" : "gap-3")}>
            <div
              className={cn(
                "w-10 h-10 aspect-square rounded-full overflow-hidden border-2 transition-all shrink-0",
                isProfileOpen && !isSidebarCollapsed ? "border-[var(--color-primary)]" : "border-transparent group-hover:border-[var(--color-primary)]"
              )}
            >
              <img
                className="w-full h-full object-cover"
                alt="Profile"
                src={user?.email === 'user@example.com' ? "https://lh3.googleusercontent.com/aida-public/AB6AXuAUu-UvnXOZ2h4Yn67oztWuXr0wM-xtW9BUx39JfM970ZsFMNysq6KoE2tF1NgDJ8zioB43aS8Sz_1fwSHp_Qz41iWzlKM-n4IeHG9ULU8URNndx8Ed55zggbUa3MmlHofumoAl5w_1Jh2RfLou8-iSnvN0F7eXFMaEsGS8kfbn1kYTLYLOFcRmX8350DR32H_XoJHjolWsr_SQYlPqGzM9R0wfc3rPO3pNsiAzmEjfcrklksdDnZXc5RwkIlT2rIIJVKKAT1yoFw" : "https://lh3.googleusercontent.com/aida-public/AB6AXuDS50v-bDzSBnsD_Gk03h8AdlKkIL5blfFkaQM8sTQCpjtFG76R05j5PyBbAdpO5BerkfxKQc8-nWR_HwCzx4oij98fFmya331jHY7uLDrzSfEn1n8Pw8sJmgKH_MkWawcEoRbmPfoZeQKp-IrIC3oZWkh42jM9laLcYDK47FbYtDjZUWUYcEm6kd6K-eNNRQNbZtryPFZ7iWQbxHkA5oh7_OkYPRVg1M6r5SlCU4-MfZAR-m-9dDRL25T8_NbSI14zm8iJ9ru2Pw"}
              />
            </div>
            <div className={cn(
              "flex-1 min-w-0 transition-all duration-300 overflow-hidden whitespace-nowrap",
              isSidebarCollapsed ? "w-0 opacity-0" : "w-auto opacity-100"
            )}>
              <p className="text-sm font-bold text-[var(--color-on-surface)] truncate">{user?.email?.split('@')[0] || '사용자'}</p>
              <p className="text-[10px] text-[var(--color-on-surface-variant)] uppercase tracking-tighter">Educator</p>
            </div>
            {!isSidebarCollapsed && (
              <span className={cn(
                "material-symbols-outlined text-sm transition-colors shrink-0",
                isProfileOpen ? "text-[var(--color-primary)]" : "text-[var(--color-on-surface-variant)] group-hover:text-[var(--color-primary)]"
              )}>more_vert</span>
            )}
          </div>

          {/* Profile Menu Dropup */}
          {isProfileOpen && !isSidebarCollapsed && (
            <div className="absolute bottom-full left-0 w-full mb-2 bg-white rounded-xl shadow-xl overflow-hidden dropdown-animate-up border border-zinc-100 z-[60]">
              <button 
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-3 text-xs text-[var(--color-error)] font-semibold hover:bg-[var(--color-error-container)]/10 text-left"
              >
                <span className="material-symbols-outlined text-sm">logout</span>
                로그아웃
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
    </>
  );
}
