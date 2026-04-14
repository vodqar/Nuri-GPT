import { cn } from "../../utils/cn";

interface LoadingSpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
  color?: "primary" | "white" | "zinc";
}

export function LoadingSpinner({ 
  className, 
  size = "md", 
  color = "primary" 
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "text-lg",
    md: "text-2xl",
    lg: "text-4xl",
    xl: "text-6xl",
  };

  const colorClasses = {
    primary: "text-[var(--color-primary)]",
    white: "text-white",
    zinc: "text-zinc-400",
  };

  return (
    <div className={cn("flex items-center justify-center", className)}>
      <span className={cn(
        "material-symbols-outlined animate-spin",
        sizeClasses[size],
        colorClasses[color]
      )}>
        progress_activity
      </span>
    </div>
  );
}
