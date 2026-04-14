import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Loader2, Image as ImageIcon, Camera, PencilLine, Crop } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { analyzeTemplateImage } from '../../../services/api';
import { showToast } from '../../../components/global/ToastContainer';
import { ImageCropperModal } from '../../../components/global/ImageCropperModal';
import { TemplateStructureEditor } from './TemplateStructureEditor';

type CreationStep = 'entry' | 'image-upload' | 'analyzing' | 'editing';

interface TemplateCreationViewProps {
  onSuccess: () => void;
  onCancel?: () => void;
}

export function TemplateCreationView({ onSuccess, onCancel }: TemplateCreationViewProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState<CreationStep>('entry');
  const [track, setTrack] = useState<'image' | 'manual'>('manual');

  // 이미지 업로드 상태
  const [file, setFile] = useState<File | null>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [isCropperOpen, setIsCropperOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 편집 상태
  const [extractedStructure, setExtractedStructure] = useState<Record<string, unknown> | undefined>(undefined);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const previewUrl = file ? URL.createObjectURL(file) : null;

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setPendingFile(e.target.files[0]);
      setIsCropperOpen(true);
    }
  };

  const handleCropComplete = (croppedBlob: Blob) => {
    if (pendingFile) {
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

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => e.preventDefault();

  const handleAnalyze = async () => {
    if (!file) {
      setError('템플릿 이미지를 선택해주세요.');
      return;
    }
    setStep('analyzing');
    setError(null);
    try {
      const result = await analyzeTemplateImage(file);
      setExtractedStructure(result.structure_json);
      setStep('editing');
    } catch (err) {
      console.error('Failed to analyze template:', err);
      showToast(t('observation.errorTemplateCreate'), 'error');
      setStep('image-upload');
    }
  };

  // ── 트랙 선택 화면 ──
  if (step === 'entry') {
    return (
      <div className="space-y-6 animate-view-enter">
        <p className="text-sm text-[var(--color-on-surface-variant)]">
          템플릿을 어떻게 만들까요?
        </p>
        <div className="space-y-3">
          <button
            type="button"
            onClick={() => { setTrack('image'); setStep('image-upload'); }}
            className="w-full flex items-center gap-4 p-5 rounded-2xl bg-[var(--color-surface-container-low)] hover:bg-[var(--color-surface-container)] border border-transparent hover:border-[var(--color-primary)]/20 transition-all text-left"
          >
            <div className="w-12 h-12 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center shrink-0">
              <Camera className="w-6 h-6 text-[var(--color-primary)]" />
            </div>
            <div>
              <p className="font-bold text-[var(--color-on-surface)]">이미지로 분석하기</p>
              <p className="text-sm text-[var(--color-on-surface-variant)] mt-0.5">
                기존 양식 사진을 찍으면 AI가 항목을 자동으로 추출해요
              </p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => { setTrack('manual'); setStep('editing'); }}
            className="w-full flex items-center gap-4 p-5 rounded-2xl bg-[var(--color-surface-container-low)] hover:bg-[var(--color-surface-container)] border border-transparent hover:border-[var(--color-primary)]/20 transition-all text-left"
          >
            <div className="w-12 h-12 rounded-full bg-[var(--color-secondary)]/10 flex items-center justify-center shrink-0">
              <PencilLine className="w-6 h-6 text-[var(--color-secondary)]" />
            </div>
            <div>
              <p className="font-bold text-[var(--color-on-surface)]">직접 입력하기</p>
              <p className="text-sm text-[var(--color-on-surface-variant)] mt-0.5">
                항목을 직접 추가하고 계층 구조를 만들어요
              </p>
            </div>
          </button>
        </div>
      </div>
    );
  }

  // ── 이미지 업로드 화면 (트랙 1) ──
  if (step === 'image-upload') {
    const dropZoneClasses = [
      'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300',
      file
        ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5'
        : 'border-[var(--color-outline-variant)] hover:border-[var(--color-primary)]/50 hover:bg-[var(--color-surface-container-low)]',
    ].join(' ');

    return (
      <div className="space-y-6 animate-view-enter">
        {error && (
          <div className="p-4 bg-[var(--color-error-container)] text-[var(--color-on-error-container)] rounded-xl border border-[var(--color-error)]/20 text-sm font-medium">
            {error}
          </div>
        )}

        <div className="space-y-3">
          <label className="block text-sm font-bold text-[var(--color-primary)] tracking-wider">
            {t('observation.templateUploadLabel')}
          </label>
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
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
                    onClick={(e) => { e.stopPropagation(); setPendingFile(file); setIsCropperOpen(true); }}
                    className="py-2 px-4 rounded-lg text-xs font-bold text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 transition-colors flex items-center gap-1.5"
                  >
                    <Crop className="w-3.5 h-3.5" />
                    다시 자르기
                  </button>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setFile(null); setPendingFile(null); }}
                    className="py-2 px-4 rounded-lg text-xs font-bold text-red-500 hover:bg-red-50 transition-colors"
                  >
                    파일 삭제
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4 py-4">
                <div className="w-16 h-16 rounded-full bg-[var(--color-surface-container-high)] flex items-center justify-center text-[var(--color-on-surface-variant)]">
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
          <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
        </div>

        <footer className="pt-4 border-t border-[var(--color-outline-variant)]/30 flex gap-3">
          <button
            type="button"
            onClick={() => setStep('entry')}
            className="flex-1 py-3.5 rounded-2xl text-[var(--color-on-surface-variant)] font-bold hover:bg-[var(--color-surface-container)] transition-all"
          >
            이전
          </button>
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!file}
            className="start-btn flex-[2] py-3.5 text-white font-bold rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            AI로 분석하기
          </button>
        </footer>

        <ImageCropperModal
          isOpen={isCropperOpen}
          onClose={() => setIsCropperOpen(false)}
          imageFile={pendingFile}
          onCropComplete={handleCropComplete}
        />
      </div>
    );
  }

  // ── AI 분석 중 로딩 화면 ──
  if (step === 'analyzing') {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-16 animate-view-enter">
        <Loader2 className="w-12 h-12 animate-spin text-[var(--color-primary)]" />
        <div className="text-center">
          <p className="font-bold text-[var(--color-on-surface)] text-lg">AI가 분석 중이에요</p>
          <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">
            이미지에서 항목 구조를 추출하고 있습니다
          </p>
        </div>
      </div>
    );
  }

  // ── 구조 편집 화면 (공통) ──
  return (
    <TemplateStructureEditor
      initialStructure={extractedStructure}
      track={track}
      sourceImageFile={track === 'image' ? file ?? undefined : undefined}
      onSuccess={onSuccess}
      onCancel={() => {
        if (track === 'image') {
          setStep('image-upload');
        } else {
          if (onCancel) onCancel();
          else setStep('entry');
        }
      }}
    />
  );
}
