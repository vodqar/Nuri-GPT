import logging
import io
from typing import Optional
from PIL import Image
import google.generativeai as genai
from google.generativeai.types import generation_types

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class OcrService:
    """
    다양한 상황에서 보편적으로 재활용할 수 있는 범용 OCR 모듈.
    첨부된 이미지를 원본 형태(줄바꿈, 표 등) 그대로 마크다운 텍스트로 변환합니다.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화 시 설정(config)에서 OCR 전용 모델 정보를 불러옵니다.
        """
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. OCR functions will fail if called.")
        else:
            genai.configure(api_key=self.api_key)

        self.model_name = settings.llm_ocr_model
        self.thinking_level = settings.llm_ocr_thinking_level
        
        # Generation Config 설정
        self.generation_config = {
            "temperature": settings.llm_ocr_temperature,
        }
        
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model '{self.model_name}': {e}")
            self.model = None

    def _prepare_image(self, image_bytes: bytes) -> Image.Image:
        """
        바이트 데이터를 PIL Image 객체로 변환합니다.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Gemini API가 처리하기 좋게 RGB 모드로 변환
            if image.mode != "RGB":
                image = image.convert("RGB")
            return image
        except Exception as e:
            logger.error(f"Failed to process image bytes: {e}")
            raise ValueError(f"Invalid image format: {e}")

    def extract_text_from_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """
        이미지에서 텍스트를 추출하여 Markdown 형식으로 반환합니다.

        Args:
            image_bytes: 이미지 파일의 바이트 데이터
            mime_type: 이미지의 MIME 타입 (기본: image/jpeg)

        Returns:
            추출된 텍스트 (Markdown 형식)
        """
        if not self.model:
            raise RuntimeError("Gemini model is not initialized (missing API key?)")

        image = self._prepare_image(image_bytes)
        
        # 범용적인 OCR 추출을 위한 명확한 시스템 프롬프트 (Role 제외, 규칙 형태)
        prompt = (
            "제공된 이미지를 분석하여 텍스트를 추출해 줘.\n"
            "[작성 규칙]\n"
            "1. 이미지에 있는 텍스트를 보이는 그대로 추출할 것.\n"
            "2. 줄바꿈, 띄어쓰기, 목록 등 원래의 문서 서식과 공간적 배치를 최대한 유지하여 Markdown 형태로 출력할 것.\n"
            "3. 이미지에 표가 포함되어 있는 경우, 마크다운 표 형식으로 변환하여 출력할 것.\n"
            "4. 어떤 부가적인 설명이나 인사말도 하지 말고, 오직 추출된 텍스트만 출력할 것.\n"
            f"5. 추론 강도는 {self.thinking_level} 수준으로 유지할 것."
        )

        try:
            # 안전 설정: 문서 추출 목적이므로 필터링을 최소화
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]
            
            response = self.model.generate_content(
                [prompt, image],
                safety_settings=safety_settings
            )
            
            # 응답에 텍스트가 없는 경우 처리
            if not response.text:
                logger.warning("Gemini API returned an empty response.")
                return ""
                
            # 불필요한 마크다운 코드 블록(```markdown, ```)이 씌워져 있으면 제거
            result = response.text.strip()
            if result.startswith("```markdown"):
                result = result[len("```markdown"):].strip()
            elif result.startswith("```"):
                result = result[len("```"):].strip()
                
            if result.endswith("```"):
                result = result[:-len("```")].strip()
                
            return result
            
        except generation_types.StopCandidateException as e:
            logger.error(f"Gemini API generation stopped unexpectedly: {e}")
            raise RuntimeError(f"OCR generation failed: {e}")
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            raise RuntimeError(f"Failed to extract text from image: {e}")

    def normalize_text(self, text: str) -> str:
        """
        추출된 텍스트를 정규화합니다.
        원본 훼손을 방지하기 위해 불필요한 공백 제거나 간단한 교정만 수행합니다.
        """
        if not text:
            return ""
            
        # HTML <br> 태그를 개행 문자로 변환
        text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        
        # 연속된 빈 줄을 최대 2줄로 제한
        import re
        normalized = re.sub(r'\n{3,}', '\n\n', text)
        
        # 좌우 공백 제거
        return normalized.strip()

