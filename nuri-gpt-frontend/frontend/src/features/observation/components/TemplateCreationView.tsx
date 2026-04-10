import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Loader2, Image as ImageIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { uploadTemplate } from '../../../services/api';
import { useAuthStore } from '../../../store/authStore';
import { showToast } from '../../../components/global/ToastContainer';
import { ImageCropperModal } from '../../../components/global/ImageCropperModal';
import { Crop } from 'lucide-react';

interface TemplateCreationViewProps {
  onSuccess: () => void;
}

export function TemplateCreationView({ onSuccess }: TemplateCreationViewProps) {
  const { t } = useTranslation();
  const user = useAuthStore((state) => state.user);
  const [templateName, setTemplateName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCropperOpen, setIsCropperOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [file]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setPendingFile(e.target.files[0]);
      setIsCropperOpen(true);
    }
  };

  const handleCropComplete = (croppedBlob: Blob) => {
    if (pendingFile) {
      // 파일명을 유지하면서 새로운 File 객체 생성
      const croppedFile = new File([croppedBlob], pendingFile.name, { type: 'image/jpeg' });
      setFile(croppedFile);
    }
    setIsCropperOpen(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type.startsWith('image/')) {
        setPendingFile(droppedFile);
        setIsCropperOpen(true);
      } else {
        setError('이미지 파일만 업로드 가능합니다.');
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('템플릿 이미지를 선택해주세요.');
      return;
    }
    if (!templateName.trim()) {
      setError('템플릿 이름을 입력해주세요.');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      await uploadTemplate(file, templateName, user?.id);
      
      // Success
      showToast('템플릿 생성이 완료되었습니다', 'success');
      onSuccess();
    } catch (err) {
      console.error('Failed to create template:', err);
      setError(t('observation.errorTemplateCreate'));
    } finally {
      setIsUploading(false);
    }
  };

  const dropZoneClasses = [
    'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300',
    file
      ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5'
      : 'border-[var(--color-outline-variant)] hover:border-[var(--color-primary)]/50 hover:bg-[var(--color-surface-container-low)]',
    isUploading && 'opacity-50 cursor-not-allowed',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <form onSubmit={handleSubmit} className="space-y-8 animate-view-enter">
      {error && (
        <div className="p-4 bg-[var(--color-error-container)] text-[var(--color-on-error-container)] rounded-xl border border-[var(--color-error)]/20 text-sm font-medium">
          {error}
        </div>
      )}

      <div className="space-y-3">
        <label htmlFor="templateName" className="block text-sm font-bold text-[var(--color-primary)] tracking-wider">
          {t('observation.templateNameLabel')}
        </label>
        <input
          id="templateName"
          type="text"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          disabled={isUploading}
          placeholder={t('observation.templateNamePlaceholder')}
          className="w-full px-5 py-4 rounded-2xl bg-[var(--color-surface-container-low)] text-[var(--color-on-surface)] border-none focus:ring-2 focus:ring-[var(--color-primary)]/50 transition-all placeholder:text-[var(--color-on-surface-variant)]/40"
        />
      </div>

      <div className="space-y-3">
        <label className="block text-sm font-bold text-[var(--color-primary)] tracking-wider">
          {t('observation.templateUploadLabel')}
        </label>
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={dropZoneClasses}
        >
          {file ? (
            <div className="flex flex-col items-center gap-4">
              <div className="relative group">
                <div className="w-24 h-24 rounded-2xl overflow-hidden shadow-md ring-4 ring-white">
                  <img src={previewUrl!} alt="Preview" className="w-full h-full object-cover" />
                </div>
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl flex items-center justify-center">
                  <ImageIcon className="text-white w-8 h-8" />
                </div>
              </div>
              <div className="text-center">
                <p className="font-bold text-[var(--color-on-surface)] break-all px-4">{file.name}</p>
                <p className="text-xs text-[var(--color-on-surface-variant)] mt-1">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 mt-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setPendingFile(file);
                    setIsCropperOpen(true);
                  }}
                  disabled={isUploading}
                  className="py-2 px-4 rounded-lg text-xs font-bold text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 transition-colors flex items-center gap-1.5"
                >
                  <Crop className="w-3.5 h-3.5" />
                  다시 자르기
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    setPendingFile(null);
                  }}
                  disabled={isUploading}
                  className="py-2 px-4 rounded-lg text-xs font-bold text-red-500 hover:bg-red-50 transition-colors"
                >
                  파일 삭제
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-4">
              <div className="w-16 h-16 rounded-full bg-[var(--color-surface-container-high)] flex items-center justify-center text-[var(--color-on-surface-variant)] group-hover:scale-110 transition-transform">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <p className="font-bold text-[var(--color-on-surface)] mb-1">
                  {t('observation.templateUploadPrompt')}
                </p>
                <p className="text-sm text-[var(--color-on-surface-variant)]">
                  {t('observation.templateUploadFormats')}
                </p>
              </div>
            </div>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          disabled={isUploading}
        />
      </div>

      <footer className="mt-8 pt-6 border-t border-[var(--color-outline-variant)]/30">
        <button
          type="submit"
          disabled={isUploading || !file || !templateName.trim()}
          className="start-btn w-full py-4 text-white font-bold rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
          <span>{isUploading ? t('observation.creatingTemplate') : t('observation.createTemplateButton')}</span>
        </button>
      </footer>

      <ImageCropperModal
        isOpen={isCropperOpen}
        onClose={() => setIsCropperOpen(false)}
        imageFile={pendingFile}
        onCropComplete={handleCropComplete}
      />
    </form>
  );
}
