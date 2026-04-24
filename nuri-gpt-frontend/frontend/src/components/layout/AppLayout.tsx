import { Outlet } from 'react-router-dom';
import { SideNavBar } from './SideNavBar';
import { MobileNavBar } from './MobileNavBar';
import { useLayoutStore } from '../../store/layoutStore';
import { cn } from '../../utils/cn';

export function AppLayout() {
  const { isSidebarCollapsed } = useLayoutStore();

  return (
    <div className="min-h-screen bg-[var(--color-surface)] text-[var(--color-on-surface)] flex flex-col font-body overflow-x-hidden">
      <div className="flex flex-1">
        <SideNavBar />
        <main className={cn(
          "flex-1 pb-20 md:pb-0 pt-[68px] md:pt-6 transition-all duration-300 ease-in-out w-full",
          isSidebarCollapsed ? "md:pl-20" : "md:pl-[280px]"
        )}>
          <Outlet />
        </main>
      </div>
      <MobileNavBar />
    </div>
  );
}
