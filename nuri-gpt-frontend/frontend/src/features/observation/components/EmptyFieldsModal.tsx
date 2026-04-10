import { AlertCircle } from 'lucide-react';
import { Modal } from '../../../components/global/Modal';

interface EmptyFieldsModalProps {
  isOpen: boolean;
  emptyFields: string[];
  onConfirm: () => void;
  onCancel: () => void;
}

export function EmptyFieldsModal({ isOpen, emptyFields, onConfirm, onCancel }: EmptyFieldsModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      showCloseButton={false}
      primaryAction={{
        label: '진행하기',
        onClick: onConfirm,
        variant: 'primary',
      }}
      secondaryAction={{
        label: '취소',
        onClick: onCancel,
      }}
    >
      <div className="flex items-center gap-4 mb-4 mt-2">
        <div className="w-12 h-12 rounded-full flex items-center justify-center shrink-0 bg-[var(--color-warning-container,var(--color-secondary-container))] text-[var(--color-on-warning-container,var(--color-on-secondary-container))]">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--color-on-surface)]">빈 칸 확인</h3>
          <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">
            다음 항목의 내용이 입력되지 않았습니다. 그래도 일지 생성을 진행하시겠습니까?
          </p>
        </div>
      </div>
      
      <div className="bg-[var(--color-surface-container-low)] rounded-xl p-4 mb-2 max-h-40 overflow-y-auto">
        <ul className="list-disc list-inside text-sm text-[var(--color-on-surface-variant)] space-y-1">
          {emptyFields.map((field, idx) => {
            const parts = field.split('.');
            const name = parts[parts.length - 1];
            return <li key={idx}>{name}</li>;
          })}
        </ul>
      </div>
    </Modal>
  );
}
