import heic2any from 'heic2any';

/**
 * 전송받은 파일이 HEIC/HEIF 포맷인지 확인하고, 
 * 맞다면 JPEG Blob으로 변환하여 반환합니다.
 * 아니라면 원본 데이터를 그대로 반환합니다.
 */
export async function ensureBrowserImage(file: File): Promise<File | Blob> {
  const fileName = file.name.toLowerCase();
  const isHeic = fileName.endsWith('.heic') || fileName.endsWith('.heif') || file.type === 'image/heic' || file.type === 'image/heif';

  if (!isHeic) {
    return file;
  }

  try {
    const converted = await heic2any({
      blob: file,
      toType: 'image/jpeg',
      quality: 0.8,
    });

    // heic2any는 결과로 단일 Blob 또는 Blob[]을 반환할 수 있음
    const resultBlob = Array.isArray(converted) ? converted[0] : converted;
    
    // 파일명을 유지하기 위해 새로운 File 객체로 감싸서 반환 (Blob으로도 충분하지만 일관성을 위해)
    const newFileName = file.name.replace(/\.(heic|heif)$/i, '.jpg');
    return new File([resultBlob], newFileName, { type: 'image/jpeg' });
  } catch (error) {
    console.error('HEIC conversion failed:', error);
    // 변환 실패 시 원본이라도 반환 (브라우저에서 안 보일 가능성이 큼)
    return file;
  }
}

/**
 * 이미지 소스(URL 또는 Blob)를 받아 지정된 각도로 회전시킨 후 새로운 Blob을 반환합니다.
 */
export async function rotateImageSource(
  imageSrc: string,
  rotation: number
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas context not available'));
        return;
      }

      // 회전된 크기 계산
      const angle = (rotation * Math.PI) / 180;
      const width = image.width;
      const height = image.height;
      const bWidth = Math.abs(Math.cos(angle) * width) + Math.abs(Math.sin(angle) * height);
      const bHeight = Math.abs(Math.sin(angle) * width) + Math.abs(Math.cos(angle) * height);

      canvas.width = bWidth;
      canvas.height = bHeight;

      ctx.translate(bWidth / 2, bHeight / 2);
      ctx.rotate(angle);
      ctx.translate(-width / 2, -height / 2);
      ctx.drawImage(image, 0, 0);

      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error('Canvas toBlob failed'));
      }, 'image/jpeg', 0.9);
    };
    image.onerror = reject;
    image.src = imageSrc;
  });
}
