/**
 * react-image-crop 좌표 변환 유틸리티
 *
 * CSS 표시 크기 기준 좌표를 원본 이미지 크기 기준 좌표로 변환
 * 회전 각도를 고려한 좌표 재계산 지원
 */

import type { PixelCrop } from 'react-image-crop';

export interface Area {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface TransformParams {
  crop: PixelCrop;
  displaySize: { width: number; height: number };
  naturalSize: { width: number; height: number };
  rotation: number; // 0, 90, 180, 270
}

/**
 * CSS 표시 크기 기준 크롭 좌표를 원본 이미지 크기 기준으로 변환
 *
 * react-image-crop은 렌더링된 DOM 요소의 크기를 기준으로 좌표를 반환하지만,
 * 실제 이미지 처리는 원본 이미지 크기(natural size)에서 이루어져야 함
 */
export function transformCropToOriginal(params: TransformParams): Area {
  const { crop, displaySize, naturalSize, rotation } = params;

  // 1. CSS 표시 크기 → 원본 이미지 크기 스케일 변환
  const scaleX = naturalSize.width / displaySize.width;
  const scaleY = naturalSize.height / displaySize.height;

  // 스케일 변환된 좌표 (회전 전 원본 기준)
  let x = crop.x * scaleX;
  let y = crop.y * scaleY;
  let width = crop.width * scaleX;
  let height = crop.height * scaleY;

  // 2. 회전 각도에 따른 좌표 변환
  // 회전된 이미지에서의 좌표를 원본 이미지 기준으로 변환
  const normalizedRotation = ((rotation % 360) + 360) % 360;

  switch (normalizedRotation) {
    case 90:
      // 90도 회전: (x, y) → (y, W - x - width)
      // 단, 여기서 W는 회전된 이미지의 너비 = 원본 높이
      return {
        x: y,
        y: naturalSize.width - x - width,
        width: height,
        height: width,
      };
    case 180:
      // 180도 회전: (x, y) → (W - x - width, H - y - height)
      return {
        x: naturalSize.width - x - width,
        y: naturalSize.height - y - height,
        width,
        height,
      };
    case 270:
      // 270도 회전: (x, y) → (H - y - height, x)
      return {
        x: naturalSize.height - y - height,
        y: x,
        width: height,
        height: width,
      };
    case 0:
    default:
      // 회전 없음: 그대로 반환
      return { x, y, width, height };
  }
}

/**
 * HTMLImageElement에서 display/natural 크기 정보 추출
 */
export function getImageSizeInfo(img: HTMLImageElement): {
  displaySize: { width: number; height: number };
  naturalSize: { width: number; height: number };
} {
  return {
    displaySize: {
      width: img.width,
      height: img.height,
    },
    naturalSize: {
      width: img.naturalWidth,
      height: img.naturalHeight,
    },
  };
}

/**
 * 회전된 이미지의 크기 정보 계산
 * 원본 크기에서 회전 후의 크기를 계산 (90/270도는 w/h swap)
 */
export function getRotatedImageSize(
  naturalSize: { width: number; height: number },
  rotation: number
): { width: number; height: number } {
  const normalizedRotation = ((rotation % 360) + 360) % 360;

  if (normalizedRotation === 90 || normalizedRotation === 270) {
    return {
      width: naturalSize.height,
      height: naturalSize.width,
    };
  }

  return { ...naturalSize };
}
