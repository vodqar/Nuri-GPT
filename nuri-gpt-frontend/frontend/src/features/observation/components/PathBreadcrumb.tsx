import { cn } from '../../../utils/cn';

interface PathBreadcrumbProps {
  path: string[];
  visibleFromIndex?: number;
}

export function PathBreadcrumb({ path, visibleFromIndex = 1 }: PathBreadcrumbProps) {
  if (path.length === 0) return null;

  let visiblePath = path.slice(visibleFromIndex);

  if (visiblePath.length === 0) {
    visiblePath = path;
  }

  return (
    <div className="field-path">
      {visiblePath.map((segment, index) => {
        const isFirst = index === 0;
        const isLast = index === visiblePath.length - 1;

        return (
          <span key={index} className="flex items-center">
            {index > 0 && <span className="path-separator">›</span>}
            <span
              className={cn(
                'path-segment',
                isFirst && 'path-segment-first',
                isLast && 'path-segment-last'
              )}
            >
              {segment}
            </span>
          </span>
        );
      })}
    </div>
  );
}
