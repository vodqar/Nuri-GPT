import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { RefreshCw, Settings } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { updateTemplateOrder } from '../../services/api';
import { useAuthStore } from '../../store/authStore';
import { TemplateCreationView } from './components/TemplateCreationView';
import { EmptyFieldsModal } from './components/EmptyFieldsModal';
import { Modal } from '../../components/global/Modal';
import { LogGenerationResultView } from './components/LogGenerationResultView';
import { TemplateSelectionView } from './components/TemplateSelectionView';
import { LogInputView } from './components/LogInputView';
import { LogGenerationHeaderRight } from './components/LogGenerationHeaderRight';
import { ViewHeader } from './components/ViewHeader';
import { getTemplateLeafKeys } from './utils/templateUtils';
import { useViewTransition } from './hooks/useViewTransition';
import { useLogGeneration } from './hooks/useLogGeneration';
import { useTemplateManagement } from './hooks/useTemplateManagement';
import { useFileUpload } from './hooks/useFileUpload';
import { CHEAT_SAMPLE_TEMPLATE, isCheatMode } from './cheat-data';
import { ImageCropperModal } from '../../components/global/ImageCropperModal';

type ViewState = 'template_selection' | 'template_creation' | 'log_generation' | 'log_result';

export function ObservationPage() {
  const { t } = useTranslation();
  const user = useAuthStore((state) => state.user);
  const { viewState, exitingView, transitionTo } = useViewTransition<ViewState>('template_selection');
  const [error, setError] = useState<string | null>(null);

  // Template management
  const {
    templates,
    setTemplates,
    selectedTemplateId,
    setSelectedTemplateId,
    isLoading: isTemplateLoading,
    isFailed: isTemplateFailed,
    isManageMode,
    hasChanges,
    fetchTemplates,
    retryFetch: retryTemplateFetch,
    handleDeleteTemplate,
    handleUpdateTemplate,
    toggleManageMode,
    exitManageModeWithoutSaving,
  } = useTemplateManagement({ userId: user?.id, setError });

  // Log generation
  const [mode, setMode] = useState<'manual' | 'auto'>('manual');
  const [manualInputs, setManualInputs] = useState<Record<string, string>>({});
  const [autoInput, setAutoInput] = useState('');
  const [childAge, setChildAge] = useState<number | null>(null);
  const [isAggressiveMode, setIsAggressiveMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [showAgeError, setShowAgeError] = useState(false);
  const [isEmptyModalOpen, setIsEmptyModalOpen] = useState(false);
  const [emptyFieldsList, setEmptyFieldsList] = useState<string[]>([]);
  const [isBackResultModalOpen, setIsBackResultModalOpen] = useState(false);
  const [isOcrCropperOpen, setIsOcrCropperOpen] = useState(false);
  const [pendingOcrFile, setPendingOcrFile] = useState<File | null>(null);

  const {
    generationHistory,
    currentHistoryIndex,
    generate,
    regenerate,
    navigateHistory,
  } = useLogGeneration({
    selectedTemplate: templates.find((t) => t.id === selectedTemplateId),
    childAge,
    isAggressiveMode,
    setIsGenerating,
    setError,
  });

  // File upload
  const onUploadSuccess = (fieldId: string, text: string) => {
    if (fieldId === 'auto') {
      setAutoInput((prev) => prev + (prev ? '\n' : '') + text);
    } else {
      setManualInputs((prev) => ({
        ...prev,
        [fieldId]: (prev[fieldId] || '') + (prev[fieldId] ? '\n' : '') + text,
      }));
    }
  };

  const { fileInputRef, processUpload, triggerUpload } = useFileUpload({
    userId: user?.id,
    setIsLoading: setIsGenerating,
    setError,
    onUploadSuccess,
  });

  const handleOcrFileSelection = (e: React.ChangeEvent<HTMLInputElement>) => {
    const pickedFile = e.target.files?.[0];
    if (pickedFile) {
      setPendingOcrFile(pickedFile);
      setIsOcrCropperOpen(true);
    }
  };

  const handleOcrCropComplete = async (croppedBlob: Blob) => {
    setIsOcrCropperOpen(false);
    if (pendingOcrFile) {
      // 업로드를 위해 Blob을 파일 객체로 전달
      await processUpload(croppedBlob);
    }
  };

  // CHEAT mode check
  useEffect(() => {
    if (isCheatMode()) {
      setTemplates([CHEAT_SAMPLE_TEMPLATE]);
      setSelectedTemplateId(CHEAT_SAMPLE_TEMPLATE.id);
      transitionTo('log_result');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);
  const semanticJson = selectedTemplate?.semantic_json || selectedTemplate?.structure_json;

  const handleManualInputChange = (field: string, value: string) => {
    setManualInputs((prev) => ({ ...prev, [field]: value }));
  };

  const handleFinalizeClick = () => {
    if (childAge === null) {
      setShowAgeError(true);
      const ageContainer = document.querySelector('.age-select-container');
      if (ageContainer) {
        ageContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    const emptyFields: string[] = [];
    if (mode === 'manual' && semanticJson) {
      const allLeafKeys = getTemplateLeafKeys(semanticJson);
      const emptyKeys = allLeafKeys.filter((key) => !manualInputs[key] || !manualInputs[key].trim());
      emptyFields.push(...emptyKeys);
    }

    if (emptyFields.length > 0) {
      setEmptyFieldsList(emptyFields);
      setIsEmptyModalOpen(true);
      return;
    }

    executeGenerate();
  };

  const executeGenerate = async () => {
    setIsEmptyModalOpen(false);

    const ocrText =
      mode === 'auto'
        ? autoInput
        : Object.entries(manualInputs)
            .filter(([, value]) => value.trim())
            .map(([key, value]) => `[${key}]\n${value}`)
            .join('\n\n');

    const result = await generate({
      template_id: selectedTemplateId,
      ocr_text: ocrText,
      child_age: childAge!,
      is_aggressive: isAggressiveMode ? 'true' : 'false',
    });

    if (result) {
      transitionTo('log_result');
    }
  };

  const handleRegenerateWithComments = async (comments: Record<string, string>) => {
    const currentResult = generationHistory[currentHistoryIndex];
    if (!currentResult) return;

    await regenerate(comments, currentResult, setIsRegenerating);
  };

  // Handle order save when manage mode ends
  const handleManageModeToggle = () => {
    if (isManageMode) {
      // Save order changes
      const orders = templates.map((t) => ({
        id: t.id,
        sort_order: t.sort_order,
      }));
      updateTemplateOrder(orders).catch(() => window.dispatchEvent(new CustomEvent('toast', { detail: { message: '순서 저장 중 오류가 발생했습니다.', type: 'error' } })));
    }
    toggleManageMode();
  };

  const handleExitManageMode = () => {
    if (hasChanges) {
      // Show cancel modal logic would go here
      // For now, just exit without saving
    }
    exitManageModeWithoutSaving?.();
  };

  return (
    <div className="p-4 sm:p-6 md:p-10 w-full max-w-4xl mx-auto">
      {/* Global loading overlay */}
      {createPortal(
        <div className={`result-loading-overlay ${(isGenerating || isRegenerating) ? 'visible' : ''}`}>
          <div className="result-loading-box scale-in">
            <RefreshCw className="w-10 h-10 animate-spin" style={{ color: 'var(--color-primary)' }} />
            <p className="font-bold text-lg" style={{ color: 'var(--color-on-surface)' }}>
              {isRegenerating ? '일지를 재생성하고 있습니다...' : '일지를 생성하고 있습니다...'}
            </p>
            <p className="text-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
              잠시만 기다려주세요
            </p>
          </div>
        </div>,
        document.body
      )}

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleOcrFileSelection}
        accept="image/*"
        className="hidden"
      />

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">
          {error}
        </div>
      )}

      <div className="space-y-6 sm:space-y-8 pt-2 sm:pt-4">
        {/* Main container */}
        <div className={`glass-panel rounded-[1.5rem] p-5 sm:p-8 shadow-sm border border-white/40 relative overflow-visible min-h-[520px] ${viewState === 'template_selection' && isManageMode ? 'edit-mode-container' : ''}`}>
          {/* Header - View specific */}
          {viewState === 'template_selection' && (
            <ViewHeader
              backIcon={isManageMode ? 'close' : 'none'}
              title={t('observation.templateSelection')}
              rightContent={
                <button
                  onClick={handleManageModeToggle}
                  className={`manage-btn ${isManageMode ? 'manage-btn-active' : ''}`}
                >
                  <Settings className="w-4 h-4" />
                  <span>{isManageMode ? t('observation.templateManageDone') : t('observation.templateManage')}</span>
                </button>
              }
              onBack={isManageMode ? handleExitManageMode : undefined}
            />
          )}

          {viewState === 'template_creation' && (
            <ViewHeader
              backIcon="arrowLeft"
              title={t('observation.createTemplateTitle')}
              onBack={() => transitionTo('template_selection')}
              disabled={isGenerating}
            />
          )}

          {viewState === 'log_generation' && (
            <ViewHeader
              title={selectedTemplate?.name || '일지 작성'}
              onBack={() => transitionTo('template_selection')}
              rightContent={
                <LogGenerationHeaderRight
                  isAggressiveMode={isAggressiveMode}
                  setIsAggressiveMode={setIsAggressiveMode}
                  mode={mode}
                  setMode={setMode}
                />
              }
            />
          )}

          {viewState === 'log_result' && (
            <ViewHeader
              backIcon="arrowLeft"
              title="생성 결과 확인"
              onBack={() => setIsBackResultModalOpen(true)}
            />
          )}

          {/* Content - Animated */}
          <div className={exitingView ? 'animate-view-exit' : 'animate-view-enter'}>
            {viewState === 'template_selection' && (
              <TemplateSelectionView
                templates={templates}
                selectedTemplateId={selectedTemplateId}
                onSelectTemplate={setSelectedTemplateId}
                onCreateNew={() => transitionTo('template_creation')}
                onStart={() => transitionTo('log_generation')}
                onTemplatesChange={setTemplates}
                onDeleteTemplate={handleDeleteTemplate}
                onUpdateTemplate={handleUpdateTemplate}
                isManageMode={isManageMode}
                onManageModeChange={toggleManageMode}
                hasChanges={hasChanges}
                onHasChangesChange={() => { /* handled in hook */ }}
                isLoading={isTemplateLoading}
                isFailed={isTemplateFailed}
                onRetry={retryTemplateFetch}
              />
            )}

            {viewState === 'template_creation' && (
              <TemplateCreationView
                onSuccess={() => {
                  fetchTemplates();
                  transitionTo('template_selection');
                }}
              />
            )}

            {viewState === 'log_generation' && (
              <LogInputView
                semanticJson={semanticJson as Record<string, unknown>}
                isTemplateLoading={isTemplateLoading}
                isGenerating={isGenerating}
                childAge={childAge}
                setChildAge={setChildAge}
                showAgeError={showAgeError}
                setShowAgeError={setShowAgeError}
                mode={mode}
                manualInputs={manualInputs}
                onManualInputChange={handleManualInputChange}
                autoInput={autoInput}
                setAutoInput={setAutoInput}
                triggerUpload={triggerUpload}
                onFinalizeClick={handleFinalizeClick}
                isAggressiveMode={isAggressiveMode}
              />
            )}

            {viewState === 'log_result' && (
              <LogGenerationResultView
                history={generationHistory}
                currentIndex={currentHistoryIndex}
                onNavigateHistory={navigateHistory}
                onRegenerate={handleRegenerateWithComments}
                isRegenerating={isRegenerating}
              />
            )}
          </div>
        </div>

        {/* Empty Fields Modal */}
        <EmptyFieldsModal
          isOpen={isEmptyModalOpen}
          emptyFields={emptyFieldsList}
          onConfirm={executeGenerate}
          onCancel={() => setIsEmptyModalOpen(false)}
        />

        {/* Back Confirmation Modal */}
        <Modal
          isOpen={isBackResultModalOpen}
          onClose={() => setIsBackResultModalOpen(false)}
          title="작성 중인 내용이 사라집니다"
          description="뒤로 가면 현재 작성 중인 코멘트 내용이 사라집니다. 계속하시겠습니까?"
          primaryAction={{
            label: '뒤로 가기',
            onClick: () => {
              setIsBackResultModalOpen(false);
              transitionTo('log_generation');
            },
            variant: 'danger',
          }}
          secondaryAction={{
            label: '취소',
            onClick: () => setIsBackResultModalOpen(false),
          }}
        />

        <ImageCropperModal
          isOpen={isOcrCropperOpen}
          onClose={() => setIsOcrCropperOpen(false)}
          imageFile={pendingOcrFile}
          onCropComplete={handleOcrCropComplete}
        />
      </div>
    </div>
  );
}
