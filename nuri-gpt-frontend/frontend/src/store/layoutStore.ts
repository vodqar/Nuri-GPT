import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface LayoutState {
  isSidebarCollapsed: boolean;
  isMobileMenuOpen: boolean;
  toggleSidebar: () => void;
  toggleMobileMenu: () => void;
  closeMobileMenu: () => void;
}

export const useLayoutStore = create<LayoutState>()(
  persist(
    (set) => ({
      isSidebarCollapsed: false,
      isMobileMenuOpen: false,
      toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
      toggleMobileMenu: () => set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),
      closeMobileMenu: () => set({ isMobileMenuOpen: false }),
    }),
    {
      name: 'layout-storage',
      partialize: (state) => ({ isSidebarCollapsed: state.isSidebarCollapsed }), // 모바일 메뉴 상태는 저장하지 않음
    }
  )
);
