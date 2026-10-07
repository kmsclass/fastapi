import os
from dataclasses import dataclass,field

# 환경변수에 여러개값을 ,로 연결하여 저장된 경우 
# ,로 분리하여 list로 리턴
def _get_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)  #환경변수에서 조회
    #[http://localhost:5173, http://127.0.0.1:5173]
    return [item.strip() for item in raw.split(",") if item.strip()]

#설정값 모음
#frozen=True : 생성 후 변경 불가
@dataclass(frozen=True)
class Settings :
    # Hugging Face Hub 의 모델 ID. 처음 실행 시 자동으로 다운로드되며
    # 이후에는 ~/.cache/huggingface/hub 에 저장된 파일을 재사용합니다.
    #   - Qwen/Qwen2.5-0.5B-Instruct : 약 1GB, CPU에서 빠름, 품질은 낮음
    #   - Qwen/Qwen2.5-1.5B-Instruct : 약 3GB, CPU에서 쓸만한 속도/품질 (기본값)
    #   - Qwen/Qwen2.5-3B-Instruct   : 약 6GB, GPU 권장
    #   - Qwen/Qwen2.5-7B-Instruct   : 약 15GB, GPU(16GB 이상) 권장
    model_id: str = os.getenv("MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")
    device: str = os.getenv("DEVICE", "auto")
    #한번에 생성할 수 있는 토큰의 수 
    max_new_tokens: int = int(os.getenv("MAX_NEW_TOKENS", "512"))
    #창의성(0.1 ~ 1.5) 낮을 수록 일관된 답변실행
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    #단어 선정시 후보단어 안에서 고르는 확률 (0 ~ 1)
    top_p: float = float(os.getenv("TOP_P", "0.8"))
    #같은 말을 반복하는 현상을 줄임 (1.0 = 사용안함)
    repetition_penalty: float = float(os.getenv("REPETITION_PENALTY", "1.05"))
    #기억할 대화 갯수. 오래된 대화의 기억은 삭제
    max_history: int = int(os.getenv("MAX_HISTORY", "20"))
    #시스템 프롬프트 : LLM의 역할 정의
    system_prompt: str = os.getenv(
        "SYSTEM_PROMPT",
        "당신은 친절하고 정확한 한국어 AI 도우미입니다. "
        "사용자의 질문에 한국어로 간결하고 이해하기 쉽게 답변하세요.",
    )
    #--------------------------------------------------------
    # cors(Cross-Origin Resource-Sharing) 관련 설정
    # 교차 리소스 공유 
    # 다른 사이트에서 현재프로젝트를 호출할 수 있는 주소 목록 설정.
    # React개발 서버에서 호출이 가능하도록 주소 등록
    cors_origins: list[str] = field(
        default_factory=lambda: _get_list(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        )
    )

settings = Settings()

