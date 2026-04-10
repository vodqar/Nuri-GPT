import { useState, useRef, useEffect, useCallback } from 'react';
import ReactCrop, { type Crop, type PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { RotateCw, Scissors } from 'lucide-react';
import { Modal } from './Modal';
import { getCroppedImg } from '../../utils/cropImage';
import { ensureBrowserImage, rotateImageSource } from '../../utils/imageFormatUtils';
import {
  transformCropToOriginal,
  getRotatedImageSize,
} from '../../utils/cropCoordinateTransform';
import { cn } from '../../utils/cn';

interface ImageCropperModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageFile: File | null;
  onCropComplete: (croppedBlob: Blob) => void;
}

export function ImageCropperModal({
  isOpen,
  onClose,
  imageFile,
  onCropComplete,
}: ImageCropperModalProps) {
  const [baseImageSrc, setBaseImageSrc] = useState<string | null>(null); // 원본(HEIC 변환본)
  const [currentImageSrc, setCurrentImageSrc] = useState<string | null>(null); // 현재 회전된 이미지
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
  const [rotation, setRotation] = useState(0); // 0, 90, 180, 270
  const [isProcessing, setIsProcessing] = useState(false);
  
  const imgRef = useRef<HTMLImageElement>(null);

  // 이미지 파일 로드 및 전처리
  useEffect(() => {
    if (!imageFile || !isOpen) {
      setBaseImageSrc(null);
      setCurrentImageSrc(null);
      setRotation(0);
      setCrop(undefined);
      return;
    }

    let objectUrl: string | null = null;

    const prepareImage = async () => {
      setIsProcessing(true);
      try {
        const processedFile = await ensureBrowserImage(imageFile);
        objectUrl = URL.createObjectURL(processedFile);
        setBaseImageSrc(objectUrl);
        setCurrentImageSrc(objectUrl); // 초기 상태는 원본과 동일
      } catch (err) {
        console.error('Image preparation failed:', err);
      } finally {
        setIsProcessing(false);
      }
    };

    prepareImage();

    return () => {
      // 컴포넌트 언마운트 시에만 정리 (회전 시 생성된 다른 Blob URL들은 별도로 관리 필요)
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [imageFile, isOpen]);

  // 회전 처리: baseImageSrc를 기준으로 cumulative rotation 적용
  const handleRotate = useCallback(async () => {
    if (!baseImageSrc) return;

    setIsProcessing(true);
    const nextRotation = (rotation + 90) % 360;
    
    try {
      // 원본을 기준으로 누적 각도만큼 회전시킨 새 블롭 생성
      const rotatedBlob = await rotateImageSource(baseImageSrc, nextRotation);
      const newUrl = URL.createObjectURL(rotatedBlob);
      
      // 이전의 currentImageSrc가 baseImageSrc와 다르다면 메모리 해제
      if (currentImageSrc && currentImageSrc !== baseImageSrc) {
        URL.revokeObjectURL(currentImageSrc);
      }
      
      setCurrentImageSrc(newUrl);
      setRotation(nextRotation);
      setCrop(undefined); // 크기 조절을 위해 영역 초기화
    } catch (err) {
      console.error('Rotation failed:', err);
    } finally {
      setIsProcessing(false);
    }
  }, [baseImageSrc, currentImageSrc, rotation]);

  // 이미지 로드 완료 시 기본 크롭 영역 설정
  const onImageLoad = () => {
    setCrop({
      unit: '%',
      width: 80,
      height: 80,
      x: 10,
      y: 10
    });
  };

  const handleConfirmCrop = async () => {
    if (!currentImageSrc || !completedCrop || !imgRef.current || !baseImageSrc) return;

    setIsProcessing(true);
    try {
      // 원본 이미지 크기 정보 가져오기 (회전 전 기준)
      const originalImg = await new Promise<HTMLImageElement>((resolve) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.src = baseImageSrc;
      });
      const originalSize = {
        width: originalImg.naturalWidth,
        height: originalImg.naturalHeight,
      };

      // 현재 표시된 이미지의 크기 정보
      const displaySize = {
        width: imgRef.current.width,
        height: imgRef.current.height,
      };

      // 회전된 경우의 이미지 크기 계산
      const rotatedSize = getRotatedImageSize(originalSize, rotation);

      // 좌표 변환: CSS 표시 크기 기준 → 원본 이미지 크기 기준
      const transformedCrop = transformCropToOriginal({
        crop: completedCrop,
        displaySize,
        // 회전된 이미지의 natural 크기는 rotatedSize와 같음
        naturalSize: rotatedSize,
        rotation,
      });

      // 회전된 이미지에서 크롭 수행 (이미 회전되어 있으므로 rotation=0)
      const croppedBlob = await getCroppedImg(currentImageSrc, transformedCrop);

      if (croppedBlob) {
        onCropComplete(croppedBlob);
        onClose();
      }
    } catch (e) {
      console.error('Failed to crop image:', e);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="이미지 영역 선택"
      showCloseButton={!isProcessing}
      maxWidth="lg"
    >
      <style>{`
        /* 핸들 커스터마이징 - 더 크고 버튼처럼 보이게 */
        .ReactCrop__drag-handle {
          width: 14px !important;
          height: 14px !important;
          background-color: var(--color-primary, #3b82f6) !important;
          border: 2px solid white !important;
          border-radius: 4px !important;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        }
        .ReactCrop__crop-selection {
          border: 2px solid var(--color-primary, #3b82f6) !important;
          box-shadow: 0 0 0 9999em rgba(0, 0, 0, 0.5) !important; /* 배경 어둡게 */
        }
      `}</style>
      
      <div className="flex flex-col gap-6 -mt-2">
        {/* 크로퍼 컨테이너 */}
        <div className="relative w-full min-h-[400px] max-h-[70vh] bg-black rounded-xl overflow-hidden flex items-center justify-center">
          {currentImageSrc ? (
            <ReactCrop
              crop={crop}
              onChange={(c) => setCrop(c)}
              onComplete={(c) => setCompletedCrop(c)}
              className="max-w-full max-h-full"
            >
              <img
                ref={imgRef}
                src={currentImageSrc}
                alt="Crop Target"
                onLoad={onImageLoad}
                style={{ 
                  maxHeight: '60vh',
                  objectFit: 'contain',
                  pointerEvents: 'none'
                }}
              />
            </ReactCrop>
          ) : (
            <div className="flex items-center justify-center h-[400px] text-gray-400 text-sm">
              {isProcessing ? '이미지 처리 중...' : '이미지를 불러오는 중입니다.'}
            </div>
          )}
        </div>

        {/* 조작 버튼 */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <button
            onClick={handleRotate}
            disabled={isProcessing || !currentImageSrc}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all duration-200 whitespace-nowrap",
              "bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-highest)]",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            <RotateCw className="w-5 h-5" />
            <span>이미지 회전</span>
          </button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={onClose}
              disabled={isProcessing}
              className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl font-medium text-[var(--color-on-surface-variant)] hover:bg-[var(--color-surface-container-low)] transition-colors whitespace-nowrap"
            >
              취소
            </button>
            <button
              onClick={handleConfirmCrop}
              disabled={isProcessing || !currentImageSrc || !completedCrop}
              className={cn(
                "flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl font-bold transition-all duration-200 whitespace-nowrap",
                "bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-dim)] shadow-lg shadow-blue-500/10",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              <Scissors className="w-5 h-5" />
              <span>영역 자르기 완료</span>
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
