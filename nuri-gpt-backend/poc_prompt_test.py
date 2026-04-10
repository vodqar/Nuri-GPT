import json
import logging
from app.services.document_template_service import DocumentTemplateService
import google.generativeai as genai
from app.core.config import get_settings

genai.configure(api_key=get_settings().gemini_api_key)

with open('poc_kordoc_output.json', 'r', encoding='utf-8') as f:
    kordoc_data = json.load(f)

# Use the modified prompt directly
model = genai.GenerativeModel(get_settings().llm_document_model)

system_instruction = (
    "제공된 보육일지 양식의 JSON 데이터(표의 셀 및 병합 정보 포함)를 분석하여, "
    "교사가 매일 내용을 입력해야 하는 항목들의 '계층 구조(대분류-중분류-소분류)'를 JSON 형식으로 추출해 줘.\n\n"
    "[작성 규칙]\n"
    "1. 표의 컬럼 헤더(예: '계획 및 실행', '비고', '내용', '일과(시간)' 등)를 하위 항목(Leaf node)의 키(Key)로 반복해서 사용하지 말 것. 대신, 교사가 작성해야 할 대상(예: '등원', '간식', '실내놀이')을 키(Key)로 만들고 그 값을 빈 문자열(\"\")로 지정할 것.\n"
    "2. 항목명에 포함된 시간 정보(예: '09:00~10:00')나 불필요한 줄바꿈(\n), 괄호 안의 부연 설명 등은 제거하고, 핵심 명사(의미 있는 텍스트)만 키(Key)로 사용할 것 (예: '간식(09:30~10:00)' -> '간식').\n"
    "3. 결재란, 날짜, 날씨, 단순 안내 문구 등 매일 새로 작성할 필요가 없는 고정 데이터는 완전히 제외할 것.\n"
    "4. '보육일지'와 같이 파일명이나 문서 제목을 나타내는 단일 최상위 구조를 만들지 말고, 의미 있는 대분류(예: '일과 및 실행', '통합보육')가 최상위가 되도록 할 것.\n"
    "5. 표의 'rowSpan'과 'colSpan', 좌우 배치를 바탕으로 종속 관계를 파악할 것 (예: 좌측의 '일상생활' 하위에 '간식', '점심식사'가 포함됨).\n"
    "6. 교사가 실제로 텍스트를 입력해야 하는 가장 끝단(Leaf node)의 값(Value)은 모두 빈 문자열(\"\")로 처리할 것.\n"
    "7. 어떤 부가적인 설명이나 인사말도 출력하지 말고, 영문 Markdown 블록 없이 순수 JSON 코드 블록 하나만 출력할 것.\n\n"
    "[출력 데이터 형식 형태(참조용)]\n"
    "{\n"
    "  \"통합보육\": {\n"
    "    \"등원\": \"\",\n"
    "    \"하원\": \"\"\n"
    "  },\n"
    "  \"일과 및 실행\": {\n"
    "    \"일상생활\": {\n"
    "      \"간식\": \"\",\n"
    "      \"점심식사\": \"\",\n"
    "      \"낮잠 및 휴식\": \"\"\n"
    "    }\n"
    "  }\n"
    "}"
)

blocks_data = kordoc_data.get("blocks", [])
blocks_str = json.dumps(blocks_data, ensure_ascii=False)
prompt = f"{system_instruction}\n\n[입력 JSON 데이터]\n{blocks_str}"

generation_config = genai.types.GenerationConfig(
    response_mime_type="application/json",
    temperature=get_settings().llm_document_temperature,
)
response = model.generate_content(
    prompt,
    generation_config=generation_config
)
print(response.text)
