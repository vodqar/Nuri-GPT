import { FileText } from 'lucide-react';

interface DynamicTemplateFormProps {
  data: Record<string, unknown>;
  path?: string[];
  inputs: Record<string, string>;
  onChange: (path: string, value: string) => void;
  onOcrUpload: (path: string) => void;
  isLoading?: boolean;
}

function getContainerStyle(depth: number): string {
  switch (depth) {
    case 0:
      return 'bg-[var(--color-surface)] rounded-2xl p-6 shadow-sm border border-[var(--color-outline)]/10';
    case 1:
      return 'bg-[var(--color-surface-container-low)]/50 rounded-xl p-5 mt-4';
    case 2:
      return 'border-l-4 border-[var(--color-primary)]/30 pl-4 mt-3';
    default:
      return 'mt-2';
  }
}

function getTitleStyle(depth: number): string {
  switch (depth) {
    case 0:
      return 'text-2xl font-bold text-[var(--color-on-surface)] font-headline mb-4';
    case 1:
      return 'text-lg font-bold text-[var(--color-primary)] uppercase tracking-wide';
    case 2:
      return 'text-base font-semibold text-[var(--color-on-surface)]';
    default:
      return 'text-sm font-medium text-[var(--color-on-surface-variant)]';
  }
}

export function DynamicTemplateForm({
  data,
  path = [],
  inputs,
  onChange,
  onOcrUpload,
  isLoading = false,
}: DynamicTemplateFormProps) {
  const depth = path.length;

  return (
    <div className={getContainerStyle(depth)}>
      {Object.entries(data).map(([key, value]) => {
        const currentPath = [...path, key];
        const flatKey = currentPath.join('.');

        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
          // 중간 노드 (카테고리)
          return (
            <div key={flatKey} className="mb-6 last:mb-0">
              <h3 className={getTitleStyle(depth)}>{key}</h3>
              <DynamicTemplateForm
                data={value as Record<string, unknown>}
                path={currentPath}
                inputs={inputs}
                onChange={onChange}
                onOcrUpload={onOcrUpload}
                isLoading={isLoading}
              />
            </div>
          );
        } else {
          // 단말 노드 (텍스트 입력)
          const displayValue = Array.isArray(value) ? value.join(', ') : String(value);
          
          return (
            <section key={flatKey} className="relative mb-4 last:mb-0">
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-bold text-[var(--color-primary)] uppercase tracking-wider">
                  {key}
                </label>
                <button
                  onClick={() => onOcrUpload(flatKey)}
                  disabled={isLoading}
                  className="ocr-btn text-xs px-3 py-1.5"
                >
                  <FileText className="w-4 h-4" />
                  OCR 업로드
                </button>
              </div>
              <textarea
                value={inputs[flatKey] || ''}
                onChange={(e) => onChange(flatKey, e.target.value)}
                placeholder={`${key} 내용을 입력하세요... (원본: ${displayValue})`}
                className="input-textarea min-h-[120px]"
              />
            </section>
          );
        }
      })}
    </div>
  );
}
