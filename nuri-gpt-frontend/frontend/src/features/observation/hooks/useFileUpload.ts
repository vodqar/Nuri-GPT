import { useState, useRef, useCallback } from 'react';
import { uploadOcr } from '../../../services/api';

interface UseFileUploadProps {
  userId?: string;
  setIsLoading: (value: boolean) => void;
  setError: (error: string | null) => void;
  onUploadSuccess?: (fieldId: string, text: string) => void;
}

export function useFileUpload({
  userId,
  setIsLoading,
  setError,
  onUploadSuccess,
}: UseFileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeUploadField, setActiveUploadField] = useState<string | null>(null);

  const processUpload = useCallback(
    async (file: File | Blob) => {
      try {
        setIsLoading(true);
        // API 서비스에서 userId를 더 이상 매개변환로 받지 않으므로 제거 (JWT 사용)
        const response = (await uploadOcr(file as File)) as { extracted_text: string };

        if (activeUploadField && onUploadSuccess) {
          onUploadSuccess(activeUploadField, response.extracted_text);
        }
      } catch (err) {
        console.error('OCR Upload failed:', err);
        setError('파일 업로드 및 텍스트 변환에 실패했습니다.');
      } finally {
        setIsLoading(false);
        setActiveUploadField(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    },
    [activeUploadField, userId, setIsLoading, setError, onUploadSuccess]
  );

  const triggerUpload = useCallback(
    (fieldId: string) => {
      setActiveUploadField(fieldId);
      fileInputRef.current?.click();
    },
    []
  );

  return {
    fileInputRef,
    activeUploadField,
    processUpload,
    triggerUpload,
  };
}
