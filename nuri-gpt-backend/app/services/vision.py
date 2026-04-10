import logging
import json
from typing import Dict, Any, Optional
import google.generativeai as genai

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_settings().gemini_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # User specified "Gemini 3.1 flash light"
        self.model_name = get_settings().llm_vision_model
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model '{self.model_name}': {e}")
            self.model = None

    def extract_template_structure(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        if not self.model:
            raise RuntimeError("Gemini model is not initialized.")
        
        system_instruction = """
            "제공된 보육일지 빈 양식 이미지를 분석하여, 교사가 매일 내용을 입력해야 하는 항목들의 '계층 구조(대분류-중분류-소분류)'를 JSON 형식으로 추출해 줘."
            "[작성 규칙]\n"
            "1. 표의 시각적인 레이아웃(선, 병합된 셀)을 바탕으로 상하위 종속 관계를 파악해 계층형 뎁스(Depth)를 구성할 것.\n"
            "2. 결재란, 날짜, 시간, 날씨, 단순 안내 문구(예: '사진자료', '예시' 등) 같이 매일 새로 작성할 필요가 없는 고정 데이터는 완전히 제외할 것.\n"
            "3. 교사가 실제로 텍스트를 입력해야 하는 가장 끝단(Leaf node)의 값(Value)은 모두 빈 문자열(\"\")로 처리할 것.\n"
            "4. 어떤 부가적인 설명이나 인사말도 하지 말고, 오직 완성된 JSON 코드 블록 하나만 출력할 것.\n"
            "5. JSON 구조의 순서는 문서의 시각적 흐름(위에서 아래로, 왼쪽에서 오른쪽)에 맞춰 순서대로 출력할 것.\n"
            "6. 요일이 포함된 경우(월~금), 반드시 '월요일', '화요일', '수요일', '목요일', '금요일' 형태의 풀네임을 사용할 것. '월', '화' 등의 축약형은 사용하지 말 것."
            "7. 시간과 제목이 병기된 경우 시간은 제거하고 제목만 키(Key) 값으로 사용할 것."

            [기대하는 JSON 구조 예시]
            // 주의: 아래의 분류명은 예시일 뿐이며, 절대 그대로 출력하지 말 것. 반드시 실제 이미지에 적힌 텍스트를 추출하여 Key 값으로 사용할 것.
            // 문서의 실제 계층 깊이(Depth)에 맞춰 유연하게 객체를 구성할 것.
            {
            "[문서 내 가장 큰 분류 텍스트 1]": {
                "[하위 분류 텍스트 A]": "",
                "[하위 분류 텍스트 B]": {
                "[최하위 분류 텍스트 a]": "",
                "[최하위 분류 텍스트 b]": ""
                }
            },
            "[문서 내 가장 큰 분류 텍스트 2]": {
                "[하위 분류 텍스트 C]": ""
            }
        """
        
        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }

        try:
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=get_settings().llm_vision_temperature,
            )
            response = self.model.generate_content(
                [system_instruction, image_part],
                generation_config=generation_config
            )
            text = response.text
            if not text:
                return {}
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
            
        except Exception as e:
            logger.error(f"Failed from Vision LLM: {e}")
            raise RuntimeError(f"Vision API parsing failed: {e}")
