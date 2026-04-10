import pytest
import io
from PIL import Image
from unittest.mock import patch, MagicMock

from app.services.ocr import OcrService
from google.generativeai.types import generation_types

# --- Fixtures ---

@pytest.fixture
def mock_settings():
    """Gemini API 키가 설정된 가짜 Settings를 제공합니다."""
    with patch("app.services.ocr.get_settings") as mock:
        mock.return_value.gemini_api_key = "fake_api_key"
        mock.return_value.llm_ocr_model = "gemini-3.1-flash-lite-preview"
        mock.return_value.llm_ocr_temperature = 1.0
        mock.return_value.llm_ocr_thinking_level = "medium"
        yield mock

@pytest.fixture
def mock_genai():
    """google.generativeai 패키지의 의존성을 모킹합니다."""
    with patch("app.services.ocr.genai") as mock:
        yield mock

@pytest.fixture
def ocr_service(mock_settings, mock_genai):
    """테스트용 OcrService 인스턴스를 생성합니다."""
    return OcrService(api_key="fake_api_key")

@pytest.fixture
def dummy_image_bytes():
    """1x1 픽셀 크기의 테스트용 이미지 바이트를 생성합니다."""
    image = Image.new("RGB", (1, 1), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


# --- Tests ---

def test_ocr_service_initialization(mock_settings, mock_genai):
    """
    OcrService 초기화 시, 설정된 API 키를 바탕으로
    genai.configure와 GenerativeModel이 올바르게 호출되는지 확인합니다.
    """
    service = OcrService(api_key="test_key")
    
    mock_genai.configure.assert_called_once_with(api_key="test_key")
    mock_genai.GenerativeModel.assert_called_once_with(
        model_name="gemini-3.1-flash-lite-preview",
        generation_config={"temperature": 1.0}
    )
    assert service.api_key == "test_key"
    assert service.model is not None


def test_prepare_image_success(ocr_service, dummy_image_bytes):
    """
    _prepare_image 메서드가 올바른 바이트 데이터를 받아
    PIL Image 객체(RGB 모드)를 반환하는지 확인합니다.
    """
    image = ocr_service._prepare_image(dummy_image_bytes)
    assert isinstance(image, Image.Image)
    assert image.mode == "RGB"
    assert image.size == (1, 1)


def test_prepare_image_failure(ocr_service):
    """
    손상되거나 유효하지 않은 바이트 데이터 입력 시
    ValueError를 발생하는지 확인합니다.
    """
    with pytest.raises(ValueError, match="Invalid image format"):
        ocr_service._prepare_image(b"invalid_bytes_data")


def test_extract_text_from_image_success(ocr_service, dummy_image_bytes, mock_genai):
    """
    extract_text_from_image가 정상적으로 이미지를 받아
    Gemini 모델의 generate_content를 호출하고 텍스트를 반환하는지 확인합니다.
    """
    # Mock Response 설정
    mock_response = MagicMock()
    mock_response.text = "```markdown\n# 추출된 텍스트\n테스트용 메모입니다.\n```"
    
    # model.generate_content의 반환값 설정
    ocr_service.model = MagicMock()
    ocr_service.model.generate_content.return_value = mock_response

    result = ocr_service.extract_text_from_image(dummy_image_bytes)

    # 반환된 텍스트 확인 (마크다운 코드 블록 제거되었는지 검증)
    assert result == "# 추출된 텍스트\n테스트용 메모입니다."
    
    # generate_content 호출 확인
    ocr_service.model.generate_content.assert_called_once()
    args, kwargs = ocr_service.model.generate_content.call_args
    
    # 호출 인자 검증 (프롬프트 텍스트, PIL Image 객체 등)
    prompt_list = args[0]
    assert isinstance(prompt_list, list)
    assert len(prompt_list) == 2
    assert "텍스트를 추출해 줘" in prompt_list[0]
    assert isinstance(prompt_list[1], Image.Image)


def test_extract_text_from_image_empty_response(ocr_service, dummy_image_bytes):
    """
    Gemini 모델이 빈 응답을 반환할 경우 빈 문자열을 반환하는지 확인합니다.
    """
    mock_response = MagicMock()
    mock_response.text = ""
    
    ocr_service.model = MagicMock()
    ocr_service.model.generate_content.return_value = mock_response

    result = ocr_service.extract_text_from_image(dummy_image_bytes)
    assert result == ""


def test_extract_text_from_image_uninitialized_model():
    """
    모델이 제대로 초기화되지 않은 상태에서 호출 시 RuntimeError를 발생하는지 확인합니다.
    """
    with patch("app.services.ocr.get_settings") as mock_settings_func:
        mock_settings_func.return_value.gemini_api_key = "fake_api_key"
        mock_settings_func.return_value.llm_ocr_model = "fake-model"
        mock_settings_func.return_value.llm_ocr_temperature = 1.0
        
        service = OcrService(api_key="fake")
        service.model = None  # 강제 초기화 실패 상태
        
        with pytest.raises(RuntimeError, match="Gemini model is not initialized"):
            service.extract_text_from_image(b"fake_bytes")


def test_normalize_text(ocr_service):
    """
    normalize_text가 불필요한 줄바꿈과 좌우 공백을 올바르게 제거하는지 확인합니다.
    """
    # 3개 이상의 줄바꿈이 있는 경우
    text_with_excessive_newlines = "첫 번째 줄\n\n\n\n\n두 번째 줄"
    expected = "첫 번째 줄\n\n두 번째 줄"
    assert ocr_service.normalize_text(text_with_excessive_newlines) == expected
    
    # 좌우 공백 제거
    text_with_spaces = "  \n  텍스트 양쪽 공백  \n  "
    assert ocr_service.normalize_text(text_with_spaces) == "텍스트 양쪽 공백"
    
    # None 또는 빈 문자열
    assert ocr_service.normalize_text("") == ""
    assert ocr_service.normalize_text(None) == ""
