import { useLayoutStore } from '../../store/layoutStore';
import { cn } from '../../utils/cn';

export function TopNavBar() {
  const { isSidebarCollapsed } = useLayoutStore();

  return (
    <header
      className={cn(
        "hidden md:flex fixed top-0 z-40 bg-white/70 backdrop-blur-xl px-12 py-6 items-center justify-between border-b border-zinc-100 dark:border-zinc-900 shadow-sm shadow-emerald-900/5 transition-all duration-300 ease-in-out",
        isSidebarCollapsed ? "left-20" : "left-64"
      )}
      style={{ right: 0 }}
    >
      <h2 className="font-headline text-2xl font-bold text-[var(--color-on-surface)] tracking-tight">관찰 일지 작성</h2>
    </header>
  );
}
