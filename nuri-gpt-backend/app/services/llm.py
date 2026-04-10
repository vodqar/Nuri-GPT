import logging
import json
import re
from typing import Optional, Dict, Any, List

import requests
import google.generativeai as genai
from google.generativeai.types import generation_types

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class LlmService:
    """
    Gemini 2.5 Flash API를 활용하여 전처리된 OCR 텍스트와 가이드라인을 바탕으로
    구조화된 유아 관찰일지 초안(JSON)을 생성하는 서비스입니다.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화 시 API 키를 주입받거나, 설정에서 가져옵니다.
        """
        self.api_key = api_key or get_settings().gemini_api_key
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. LLM functions will fail if called.")
        else:
            genai.configure(api_key=self.api_key)

        # Gemini 2.5 Flash 모델 사용
        self.model_name = get_settings().llm_text_model
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model '{self.model_name}': {e}")
            self.model = None

    def generate_observation_log(self, ocr_text: str, additional_guidelines: str = "", is_aggressive: str = "false", child_age: int = 0) -> Dict[str, Any]:
        """
        Dify API를 사용하여 OCR/사용자 입력 메모를 기반으로 관찰일지를 생성합니다.
        스트리밍(SSE) 응답과 Blocking JSON 응답 모두를 지원합니다.
        
        Args:
            ocr_text: 사용자가 입력한 관찰 내용
            additional_guidelines: 유치원/어린이집 평가제 가이드라인 등 추가 지시사항
            
        Returns:
            구조화된 관찰일지 데이터 (JSON 파싱된 Dict)
        """
        dify_key = get_settings().dify_api_key
        dify_url = get_settings().dify_api_url
        if not dify_key:
            logger.error("DIFY_API_KEY is not set.")
            raise RuntimeError("Dify API key is not configured.")
            
        if not ocr_text or not ocr_text.strip():
            logger.warning("Empty OCR text provided for generation.")
            return self._get_empty_response()

        query_text = f"[관찰 내용]\n{ocr_text}"
        if additional_guidelines:
            query_text += f"\n\n[추가 가이드라인]\n{additional_guidelines}"

        headers = {
            "Authorization": f"Bearer {dify_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {
                "is_aggressive": is_aggressive,
                "child_age": str(child_age)
            },
            "query": query_text,
            "response_mode": "streaming",
            "conversation_id": "",
            "user": "nuri-gpt-user",
            "auto_generate_name": False
        }
        
        endpoint = f"{dify_url.rstrip('/')}/chat-messages"
        
        try:
            with requests.post(endpoint, json=payload, headers=headers, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                content_type = response.headers.get("Content-Type", "")
                answer_text = ""
                
                if "text/event-stream" in content_type:
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data: "):
                                data_str = decoded[6:]
                                try:
                                    event_data = json.loads(data_str)
                                    chunk = ""
                                    if "answer" in event_data:
                                        chunk = event_data["answer"]
                                    elif "text" in event_data:
                                        chunk = event_data["text"]
                                    elif "data" in event_data and "text" in event_data["data"]:
                                        chunk = event_data["data"]["text"]
                                        
                                    if chunk:
                                        answer_text += chunk
                                except json.JSONDecodeError:
                                    pass
                else:
                    response_json = response.json()
                    answer_text = response_json.get("answer", "") or response_json.get("text", "")
                
                if not answer_text:
                    logger.warning("Dify API returned no answer text.")
                    return self._get_empty_response()
                    
                parsed_data = self._parse_json_response(answer_text)
                
                if parsed_data is not None:
                    # JSON 구조가 {"보육일지": ...} 처럼 기존과 다를 경우 랩핑
                    if "보육일지" in parsed_data or "title" not in parsed_data:
                        fallback = self._get_empty_response()
                        fallback["title"] = "관찰일지 / 보육일지"
                        fallback["observation_content"] = json.dumps(parsed_data, ensure_ascii=False, indent=2)
                        return fallback
                    return self._validate_and_fill_response(parsed_data)
                    
                logger.error(f"Failed to parse JSON response from Dify. Text: {answer_text[:500]}")
                fallback = self._get_empty_response()
                fallback["observation_content"] = f"[JSON 파싱 오류 - 원본 응답]\n{answer_text}"
                return fallback

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Error during Dify API call: {e}")
            raise RuntimeError(f"Failed to communicate with Dify API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Dify log generation: {e}")
            raise RuntimeError(f"Failed to generate log: {e}")

    def _get_empty_response(self) -> Dict[str, Any]:
        """기본(빈) 응답 구조를 반환합니다."""
        return {
            "title": "",
            "observation_content": "",
            "evaluation_content": "",
            "development_areas": []
        }
        
    def _validate_and_fill_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """응답 데이터의 필수 키 존재 여부를 확인하고 누락된 경우 기본값으로 채웁니다."""
        expected_keys = ["title", "observation_content", "evaluation_content", "development_areas"]
        result = self._get_empty_response()
        
        for key in expected_keys:
            if key in data:
                result[key] = data[key]
                
        # development_areas가 리스트가 아닌 경우 처리
        if not isinstance(result["development_areas"], list):
            result["development_areas"] = [str(result["development_areas"])] if result["development_areas"] else []
            
        return result

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """LLM 응답의 코드 펜스(```json ... ```)를 제거합니다."""
        if not text:
            return ""

        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return cleaned.strip()

    def _safe_get_response_text(self, response: Any) -> str:
        """Gemini 응답에서 텍스트를 안전하게 추출합니다."""
        try:
            text = getattr(response, "text", None)
            if isinstance(text, str) and text.strip():
                return text.strip()
        except Exception as exc:
            logger.warning(f"Gemini response.text 접근 실패. fallback 시도: {exc}")

        try:
            candidates = getattr(response, "candidates", None) or []
            if not candidates:
                return ""

            parts = getattr(candidates[0].content, "parts", [])
            chunks: List[str] = []
            for part in parts:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str) and part_text:
                    chunks.append(part_text)

            return "".join(chunks).strip()
        except Exception as exc:
            logger.warning(f"Gemini candidates 기반 텍스트 추출 실패: {exc}")
            return ""

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Gemini 응답 문자열에서 JSON 객체를 최대한 견고하게 파싱합니다."""
        if not response_text:
            return None

        cleaned = self._strip_code_fence(response_text)
        candidates = [cleaned]

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and start < end:
            candidates.append(cleaned[start:end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        return None

    def generate_updated_activities(
        self,
        semantic_json: Dict[str, Any],
        additional_guidelines: str = "",
        supplemental_text: str = "",
        child_age: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Semantic JSON을 입력받아 target_id 기준 updated_activities를 생성합니다.

        Args:
            semantic_json: 파서에서 추출한 문맥 기반 JSON
            additional_guidelines: 추가 가이드라인
            supplemental_text: OCR 메모 등 보조 입력 텍스트
            child_age: 대상 아동 연령 (만0세~만5세)

        Returns:
            List[Dict[str, str]]: [{"target_id": "...", "updated_text": "..."}, ...]
        """
        if not self.model:
            raise RuntimeError("Gemini model is not initialized (missing API key?)")

        if not isinstance(semantic_json, dict):
            logger.warning("Invalid semantic_json payload type. Expected dict.")
            return []

        activities_raw = semantic_json.get("activities", [])
        if not isinstance(activities_raw, list):
            logger.warning("Invalid semantic_json.activities type. Expected list.")
            return []

        normalized_activities: List[Dict[str, str]] = []
        fallback_by_target_id: Dict[str, str] = {}
        ordered_target_ids: List[str] = []

        for activity in activities_raw:
            if not isinstance(activity, dict):
                continue

            target_id = str(activity.get("target_id", "")).strip()
            if not target_id:
                continue

            current_text = str(activity.get("current_text", ""))
            fallback_by_target_id[target_id] = current_text
            ordered_target_ids.append(target_id)

            normalized_activities.append(
                {
                    "category": str(activity.get("category", "")),
                    "sub_category": str(activity.get("sub_category", "")),
                    "target_id": target_id,
                    "current_text": current_text,
                }
            )

        if not normalized_activities:
            logger.warning("No valid activities found in semantic_json.")
            return []

        semantic_payload = {
            "document_type": str(semantic_json.get("document_type", "")),
            "date": str(semantic_json.get("date", "")),
            "activities": normalized_activities,
        }

        age_guideline = f"[{child_age}세의 보육일지 작성 지침을 참고합니다.]\n" if child_age is not None else ""

        system_instruction = (
            f"{age_guideline}"
            "당신은 유치원 및 어린이집의 전문 교사입니다. "
            "입력으로 제공된 Semantic JSON의 활동 문맥(category/sub_category/current_text)을 바탕으로 "
            "각 target_id에 대응하는 보육일지 문장을 수정/보완하세요.\n"
            "다음 규칙을 반드시 지키세요:\n"
            "1. 각 항목의 target_id는 입력값을 그대로 유지하세요.\n"
            "2. 제공되지 않은 target_id를 새로 만들지 마세요.\n"
            "3. 사실 왜곡/환각 없이 입력 문맥에 기반해 자연스럽게 문장을 다듬으세요.\n"
            "4. 정보가 부족하면 빈 문자열이 아니라 가능한 범위에서 current_text를 보존해 정리하세요.\n\n"
            "반드시 아래 JSON 스키마 형태의 유효한 JSON 문자열만 출력하세요. "
            "마크다운 백틱(```json)이나 설명 문장은 포함하지 마세요.\n"
            "{\n"
            '  "updated_activities": [\n'
            "    {\n"
            '      "target_id": "t_1",\n'
            '      "updated_text": "수정된 문장"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            "다음 Semantic JSON을 기준으로 updated_activities를 생성하세요.\n\n"
            f"[Semantic JSON]\n{json.dumps(semantic_payload, ensure_ascii=False, indent=2)}\n"
        )

        if supplemental_text and supplemental_text.strip():
            user_prompt += f"\n[보조 메모]\n{supplemental_text.strip()}\n"

        if additional_guidelines:
            user_prompt += f"\n[추가 가이드라인]\n{additional_guidelines}\n"

        try:
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=get_settings().llm_text_temperature,
            )

            full_prompt = f"{system_instruction}\n\n---\n\n{user_prompt}"

            response = self.model.generate_content(
                full_prompt,
                safety_settings=safety_settings,
                generation_config=generation_config,
            )

            response_text = self._safe_get_response_text(response)
            if not response_text:
                logger.warning("Gemini API returned an empty response for semantic generation.")
                return [
                    {"target_id": target_id, "updated_text": fallback_by_target_id[target_id]}
                    for target_id in ordered_target_ids
                ]

            parsed_data = self._parse_json_response(response_text)
            if parsed_data is None:
                logger.error(
                    "Failed to parse JSON response from Gemini for semantic generation. "
                    f"Response text snippet: {response_text[:500]}"
                )
                return [
                    {"target_id": target_id, "updated_text": fallback_by_target_id[target_id]}
                    for target_id in ordered_target_ids
                ]

            generated_map = dict(fallback_by_target_id)
            raw_updated_activities = parsed_data.get("updated_activities", [])

            if isinstance(raw_updated_activities, list):
                for item in raw_updated_activities:
                    if not isinstance(item, dict):
                        continue
                    target_id = str(item.get("target_id", "")).strip()
                    if target_id not in generated_map:
                        continue
                    updated_text = item.get("updated_text", "")
                    generated_map[target_id] = str(updated_text) if updated_text is not None else ""
            elif isinstance(raw_updated_activities, dict):
                for target_id, updated_text in raw_updated_activities.items():
                    key = str(target_id).strip()
                    if key in generated_map:
                        generated_map[key] = str(updated_text) if updated_text is not None else ""

            return [
                {"target_id": target_id, "updated_text": generated_map[target_id]}
                for target_id in ordered_target_ids
            ]

        except Exception as e:
            logger.error(f"Error during semantic activity generation: {e}")
            raise RuntimeError(f"Failed to generate updated activities from LLM: {e}")

    def generate_regenerated_activities(
        self,
        original_semantic_json: Dict[str, Any],
        current_activities: List[Dict[str, str]],
        comments: List[Dict[str, str]],
        additional_guidelines: str = "",
        is_aggressive: str = "false",
        child_age: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Dify Chatflow를 호출하여 코멘트 기반 부분 재생성을 수행합니다.
        기존 생성 Chatflow와 동일한 형식으로 요청을 구성합니다.

        Args:
            original_semantic_json: 최초 템플릿 Semantic JSON
            current_activities: 현재 생성된 활동 목록 [{"target_id": "...", "updated_text": "..."}, ...]
            comments: 사용자가 남긴 수정 코멘트 목록 [{"target_id": "...", "comment": "..."}, ...]
            additional_guidelines: 추가 가이드라인

        Returns:
            재생성된 updated_activities 목록 [{"target_id": "...", "updated_text": "..."}, ...]
        """
        import requests

        settings = get_settings()

        # 재생성용 API 키/URL 설정 (미설정 시 기본값 사용)
        dify_key = settings.dify_regenerate_api_key or settings.dify_api_key
        dify_url = settings.dify_regenerate_api_url or settings.dify_api_url

        if not dify_key:
            logger.error("[Dify Regenerate] DIFY_API_KEY is not set.")
            raise RuntimeError("Dify API key is not configured for regeneration.")

        # 현재 활동을 딕셔너리로 변환 (target_id -> updated_text)
        content_map: Dict[str, str] = {
            act["target_id"]: act.get("updated_text", "")
            for act in current_activities
            if act.get("target_id")
        }
        ordered_target_ids = list(content_map.keys())

        if not ordered_target_ids:
            logger.warning("[Dify Regenerate] No valid current_activities provided.")
            return []

        # 코멘트를 해당 키의 값에 삽입
        for comment in comments:
            target_id = comment.get("target_id")
            comment_text = comment.get("comment", "").strip()
            if target_id and comment_text and target_id in content_map:
                original_text = content_map[target_id]
                # 코멘트 삽입 형식: 기존 텍스트 + 수정 요청 문구
                content_map[target_id] = f'{original_text} -> 다음 내용을 반영하여 수정합니다: "{comment_text}"'
                logger.info(f"[Dify Regenerate] Comment applied to {target_id}: {comment_text[:50]}...")

        # query 필드 구성: JSON 형태의 콘텐츠 맵
        # 기존 생성 파이프라인과 동일한 형식으로 통일
        query_parts = []
        
        # 1. 관찰 메모 섹션 (current_activities를 JSON으로)
        content_json = json.dumps(content_map, ensure_ascii=False, indent=2)
        query_parts.append(f"[관찰 메모]\n{content_json}")
        
        # 2. 태그 목록 섹션 (모든 target_id를 태그로)
        tags_list = list(content_map.keys())
        tags_json = json.dumps(tags_list, ensure_ascii=False, indent=2)
        query_parts.append(f"\n[태그 목록(Tags)]\n{tags_json}")
        
        # 3. 추가 가이드라인 (있는 경우)
        if additional_guidelines:
            query_parts.append(f"\n[추가 가이드라인]\n{additional_guidelines}")
        
        query_text = "\n".join(query_parts)

        headers = {
            "Authorization": f"Bearer {dify_key}",
            "Content-Type": "application/json"
        }

        # 기존 생성 파이프라인과 동일한 payload 구조
        payload = {
            "inputs": {
                "is_aggressive": is_aggressive,
                "child_age": str(child_age) if child_age is not None else ""
            },
            "query": query_text,
            "response_mode": "streaming",
            "conversation_id": "",
            "user": "nuri-gpt-user",
            "auto_generate_name": False
        }

        endpoint = f"{dify_url.rstrip('/')}/chat-messages"

        logger.info(f"[Dify Regenerate] Request to {endpoint} | Activities: {len(current_activities)}, Comments: {len(comments)}")
        logger.debug(f"[Dify Regenerate] Query snippet: {query_text[:300]}...")

        try:
            with requests.post(endpoint, json=payload, headers=headers, stream=True, timeout=120) as response:
                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "")
                answer_text = ""

                if "text/event-stream" in content_type:
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data: "):
                                data_str = decoded[6:]
                                try:
                                    event_data = json.loads(data_str)
                                    event_type = event_data.get("event", "unknown")

                                    if event_type == "error":
                                        error_msg = event_data.get("message", "Unknown error")
                                        error_code = event_data.get("code", "N/A")
                                        logger.error(f"[Dify Regenerate] Error event: code={error_code}, message={error_msg}")
                                        continue

                                    chunk = ""
                                    if "answer" in event_data:
                                        chunk = event_data["answer"]
                                    elif "text" in event_data:
                                        chunk = event_data["text"]
                                    elif "data" in event_data and "text" in event_data["data"]:
                                        chunk = event_data["data"]["text"]

                                    if chunk:
                                        answer_text += chunk

                                except json.JSONDecodeError:
                                    pass
                else:
                    response_json = response.json()
                    answer_text = response_json.get("answer", "") or response_json.get("text", "")

                logger.info(f"[Dify Regenerate] Response completed | Length: {len(answer_text)}")

                if not answer_text:
                    logger.warning("[Dify Regenerate] Empty response, returning current activities.")
                    return [
                        {"target_id": tid, "updated_text": content_map.get(tid, "")}
                        for tid in ordered_target_ids
                    ]

                # JSON 파싱
                parsed_data = self._parse_json_response(answer_text)

                if parsed_data is None:
                    logger.error(
                        f"[Dify Regenerate] Failed to parse JSON. Response snippet: {answer_text[:500]}"
                    )
                    return [
                        {"target_id": tid, "updated_text": content_map.get(tid, "")}
                        for tid in ordered_target_ids
                    ]

                # 결과 조합 - 기존 Chatflow 응답 형식을 updated_activities 형태로 변환
                # 응답은 JSON 객체 형태 (키: target_id, 값: updated_text)
                result_map = dict(content_map)
                
                # 응답이 딕셔너리 형태인 경우 (기존 생성 Chatflow의 응답 형식)
                if isinstance(parsed_data, dict):
                    for target_id, updated_text in parsed_data.items():
                        # target_id 형태의 키만 처리 (보육일지.XXX.XXX 패턴)
                        if isinstance(target_id, str) and target_id in result_map:
                            result_map[target_id] = str(updated_text) if updated_text is not None else ""
                            logger.debug(f"[Dify Regenerate] Updated {target_id}: {str(updated_text)[:50]}...")
                


                return [
                    {"target_id": tid, "updated_text": result_map.get(tid, "")}
                    for tid in ordered_target_ids
                ]

        except requests.exceptions.RequestException as e:
            logger.error(f"[Dify Regenerate] HTTP Error: {e}")
            # fallback: 현재 활동 반환
            return [
                {"target_id": tid, "updated_text": content_map.get(tid, "")}
                for tid in ordered_target_ids
            ]
        except Exception as e:
            logger.error(f"[Dify Regenerate] Unexpected error: {e}")
            raise RuntimeError(f"Failed to regenerate activities: {e}")

    @staticmethod
    def _extract_format_tags(text: str) -> List[str]:
        """문자열에서 {{format:...}} 패턴 태그를 추출합니다."""
        if not text:
            return []

        pattern = re.compile(r"\{\{format:[^{}]+\}\}")
        seen = set()
        tags: List[str] = []
        for tag in pattern.findall(text):
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
        return tags

    def generate_journal_content(self, ocr_text: str, tags: List[str], additional_guidelines: str = "", is_aggressive: str = "false", child_age: int = 0) -> Dict[str, str]:
        """
        OCR 텍스트와 템플릿의 태그 목록(Tags)을 바탕으로,
        각 태그에 알맞은 내용을 생성하여 반환합니다.
        
        Args:
            ocr_text: 수기 메모 등에서 추출된 텍스트
            tags: 템플릿 분석을 통해 얻은 포맷 내포형 태그 목록 (예: ["{{format:time_자유놀이}}", ...])
            additional_guidelines: 유치원/어린이집 평가제 가이드라인 등 추가 지시사항
            
        Returns:
            Dict[str, str]: 태그를 키로 하고, 생성된 텍스트를 값으로 가지는 매핑 정보
        """
        if not self.model:
            raise RuntimeError("Gemini model is not initialized (missing API key?)")
            
        if not ocr_text or not ocr_text.strip():
            logger.warning("Empty OCR text provided for journal generation.")
            return {}

        if not tags:
            logger.warning("Empty tags provided for journal generation.")
            return {}

        tags_str = json.dumps(tags, ensure_ascii=False, indent=2)

        system_instruction = (
            "## Persona\n"
            "당신은 '2025년 개정 어린이집 평가 매뉴얼'을 완벽히 숙지한 보육실무 기록 전문가입니다. "
            "교사가 입력한 데이터를 바탕으로 평가제 기준에 부합하는 전문적인 보육일지를 생성하되, "
            "없는 사실을 지어내지 않는 '사실 기반의 전문성'을 유지합니다.\n\n"
            "## Core Task\n"
            "제공된 JSON 구조를 유지하며, 아래의 [정보 처리 원칙]과 [전문 기록법]을 적용하여 내용을 생성합니다.\n\n"
            "## [정보 처리 원칙] - 중요\n"
            "1. **전문적 확장 (허용)**: 사용자가 제공한 단편적인 키워드나 힌트를 보육 매뉴얼의 기준에 맞춰 "
            "전문적인 문장으로 다듬고 교육적 의미를 부여하는 것은 적극 권장됩니다.\n"
            "   - 예: \"모래 놀이함\" → \"모래의 질감을 탐색하며 자연물에 대한 호기심을 갖고 소근육을 조절하는 경험을 함.\"\n"
            "2. **사실 창조 금지 (엄격 금지)**: 입력값에 특정 항목(예: 간식 메뉴, 안전교육 주제, 기상 상황 등)에 대한 정보나 "
            "힌트가 전혀 없을 경우, 절대 새로운 사실을 지어내지 마십시오.\n"
            "3. **정보 부재 시 처리**: 입력 정보가 부족하여 특정 JSON 키(Key)의 내용을 작성할 수 없는 경우, "
            "해당 값(Value)은 \"정보 없음\"으로 기입합니다.\n\n"
            "## [전문 기록법: 톤앤매너 지침]\n"
            "1. [놀이상황 / 일상생활] - '객관적 묘사법': 영유아의 행동과 언어를 사실적으로 기록합니다.\n"
            "2. [놀이평가 / 배움의 의미] - '의미 분석법': 놀이 과정에서 나타난 발달적 변화나 통합적 경험을 분석합니다.\n"
            "3. [놀이지원 / 다음날 계획] - '비계설정 지원법': 놀이의 확장을 위한 교사의 구체적 지원 방안을 명시합니다.\n\n"
            "## 2025 개정 평가제 필수 반영 사항\n"
            "- 융통성: 미세먼지 등 기상 상황이나 영유아의 컨디션 변화가 입력되었을 때만 그 사유와 대체 활동을 기술합니다. "
            "관련 언급이 없다면 지어내지 마십시오.\n"
            "- 개별화: 장애영유아 관련 데이터가 있을 경우에만 IEP 목표와 연계하여 작성합니다.\n"
            "- 권장 어휘: '발달적 변화', '통합적 경험', '자발적 참여', '흥미의 지속', '비계 설정', '공간 재구성'.\n\n"
            "## Constraints\n"
            "- 반드시 JSON 형식으로만 답변할 것.\n"
            "- 사용자가 준 JSON 키값(Key)은 절대 수정하거나 누락하지 말 것.\n"
            "- 모든 답변은 입력된 데이터의 범주 안에서만 전문적으로 확장할 것."
        )

        user_prompt = f"[관찰 메모]\n{ocr_text}\n\n[태그 목록(Tags)]\n{tags_str}\n"

        if additional_guidelines:
            user_prompt += f"\n[추가 가이드라인]\n{additional_guidelines}\n"

        try:
            dify_key = get_settings().dify_api_key
            dify_url = get_settings().dify_api_url
            if not dify_key:
                logger.error("Dify API key is not configured.")
                raise RuntimeError("Dify API key is not configured.")

            headers = {
                "Authorization": f"Bearer {dify_key}",
                "Content-Type": "application/json"
            }
            
            # Dify 워크플로우에 시스템 프롬프트가 이미 통합되어 있으므로 user_prompt만 전송
            payload = {
                "inputs": {
                    "is_aggressive": is_aggressive,
                    "child_age": str(child_age)
                },
                "query": user_prompt,
                "response_mode": "streaming",
                "conversation_id": "",
                "user": "nuri-gpt-user",
                "auto_generate_name": False
            }
            
            endpoint = f"{dify_url.rstrip('/')}/chat-messages"
            
            logger.info(f"[Dify] Request to {endpoint} | Tags count: {len(tags)}")
            logger.debug(f"[Dify] Query snippet: {user_prompt[:200]}...")
            
            with requests.post(endpoint, json=payload, headers=headers, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                content_type = response.headers.get("Content-Type", "")
                answer_text = ""
                conversation_id = None
                
                logger.info(f"[Dify] Response started | Content-Type: {content_type}")
                
                if "text/event-stream" in content_type:
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data: "):
                                data_str = decoded[6:]
                                try:
                                    event_data = json.loads(data_str)
                                    event_type = event_data.get("event", "unknown")
                                    
                                    # 에러 이벤트 특별 처리
                                    if event_type == "error":
                                        error_msg = event_data.get("message", "Unknown error")
                                        error_code = event_data.get("code", "N/A")
                                        logger.error(f"[Dify] Error event received: code={error_code}, message={error_msg}")
                                        continue
                                    
                                    # conversation_id 추적
                                    if not conversation_id and "conversation_id" in event_data:
                                        conversation_id = event_data.get("conversation_id")
                                        logger.info(f"[Dify] Conversation ID: {conversation_id}")
                                    
                                    chunk = ""
                                    if "answer" in event_data:
                                        chunk = event_data["answer"]
                                    elif "text" in event_data:
                                        chunk = event_data["text"]
                                    elif "data" in event_data and "text" in event_data["data"]:
                                        chunk = event_data["data"]["text"]
                                    elif event_type == "message_end":
                                        logger.info(f"[Dify] Message end event received")
                                        
                                    if chunk:
                                        answer_text += chunk
                                except json.JSONDecodeError as je:
                                    logger.warning(f"[Dify] JSON decode error: {je} | data: {data_str[:100]}")
                                    pass
                else:
                    response_json = response.json()
                    answer_text = response_json.get("answer", "") or response_json.get("text", "")
                    conversation_id = response_json.get("conversation_id")
                    logger.info(f"[Dify] Non-streaming response | conversation_id: {conversation_id}")
                
                logger.info(f"[Dify] Response completed | Answer length: {len(answer_text)} | conversation_id: {conversation_id}")
                
                if not answer_text:
                    logger.warning("[Dify] API returned an empty response for journal content.")
                    return {k: "" for k in tags}
                
                # 응답 내용 일부 로깅 (디버깅용)
                logger.debug(f"[Dify] Response snippet: {answer_text[:200]}...")
                
                parsed_data = self._parse_json_response(answer_text)
                
                if parsed_data is None:
                    logger.error(
                        "[Dify] Failed to parse JSON response. "
                        f"Response text snippet: {answer_text[:500]}"
                    )
                    return {k: "" for k in tags}

                # Ensure all tags exist in the output
                result = {}
                for tag in tags:
                    result[tag] = str(parsed_data.get(tag, ""))
                return result

        except requests.exceptions.RequestException as e:
            logger.error(f"[Dify] HTTP Error: {e}")
            raise RuntimeError(f"Failed to communicate with Dify API: {e}")
        except Exception as e:
            logger.error(f"[Dify] Unexpected error: {e}")
            raise RuntimeError(f"Failed to generate journal content from LLM: {e}")
