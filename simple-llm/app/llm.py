import threading
import time
import torch  #uv add torch
from transformers import (  #uv add transformers
    AutoTokenizer,
    AutoModelForCausalLM,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer
)
from collections.abc import Iterator

from app.config import settings
from app.schemas import ChatMessage

class QwenLLM :
    def __init__(self,model_id:str) :
        self.model_id = model_id
        self.okenizer =None
        self.model = None
        #모델 1개를 여러 요청으로 동시 실행되면 성능이 저하될 우려가 있음
        # Lock() : 1개의 요청만 생성
        self._lock = threading.Lock()
    @property
    def is_ready(self) ->bool :
        return self.model is not None
    @property  #함수를 속성처럼 사용하는 경우 
    def device(self) -> str :
        return str(self.model.device) if self.model is not None else "-"
    
    # @porperty가 있으면 오류발생 
    def load(self) -> None :
        start = time.time()
        use_cuda = settings.device == 'cuda' or (
            settings.device == "auto" and torch.cuda.is_available()
        )
        # 숫자 정밀도 설정
        # - GPU : float16 . 성능이 좋음
        # - CPU : float32 : 16비트 연산이 느리고 불안정함
        dtype = "auto" if use_cuda else torch.float32
        #문장 <-> 토큰 변환
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        #모델 : 모델을 다운받음. 
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            dtype=dtype,
            device_map="auto" if use_cuda else "cpu"
        )
        #학습이 아닌 추론(사용) 모드임.
        self.model.eval()

    # Qwen 모델에서 형식문자열로 변환
    # 대화 내용을 프롬프트 문자열 변환
    # 1. 대화기록이 많으면 최근 20건까지만 남김
    # 2. 시스템 프롬프트 추가. 모델의 특성을 설정 
    def build_prompt(self, messages: list[ChatMessage]) -> str:
        recent = messages[-settings.max_history :]  # 1
        conversation = [{"role": "system", "content": settings.system_prompt}]
        #m.model_dump() : dict형태로 변경
        conversation += [m.model_dump() for m in recent]
        # 대화 -> 프롬프트 문자열로 변환
        return self.tokenizer.apply_chat_template(
            conversation, tokenize=False, add_generation_prompt=True
        )
    # generate() 함수에 사용가능하도록 dict형태로 정리
    def _generation_kwargs(
            self,
            messages : list[ChatMessage],
            max_new_tokens : int | None,
            temperature: float | None
    ) -> dict :
        prompt = self.build_prompt(messages)
        inputs = self.tokenizer(prompt,return_tensors="pt").to(self.model.device)
        temperature = settings.temperature if temperature is None else temperature
        return {
            **inputs,   #input_ids ...
            "max_new_tokens" : max_new_tokens or settings.max_new_tokens,
            "do_sample" : temperature > 0,  #True : 무작위 다음 토큰 선택. False : 1등 토큰 선택
            "temperature" : temperature if temperature > 0 else None,
            "top_p" : settings.top_p if temperature > 0 else None,
            "repetition_penalty" : settings.repetition_penalty,
            "pad_token_id" : self.tokenizer.eos_token_id # 문장끝인 경우 EOS 토큰 사용
        }

    # 답변 전체를 한번에 반환
    def generate (
       self,
       messages : list[ChatMessage],   #대화기록. 
       max_new_tokens : int | None = None, #최대 토큰수
       temperature : float | None = None      #창의성
    ) -> str :     #반환값 : LLM의 답변. (프롬프트 부분과, 특수토큰 제외. 앞뒤 공백 제거)
        # LLM에 전달한 인자를 dict 객체로 리턴
        kwargs = self._generation_kwargs(messages,max_new_tokens,temperature)
        #입력 프롬프트 갯수
        prompt_len = kwargs["input_ids"].shape[1]  #입력(프롬프트)의 토큰 개수 
        # torch.inference_mode()
        # 학습모드가 아니고 추론 전용 모드. 빠름
        with self._lock, torch.inference_mode() :
            # **kwargs : input_ids=..., ... 키워드 값으로 전달
            # output_ids : 입력값 + 응답값
            #output_ids의 모양 : [1, 프롬프트길이 + 생성된 토큰수]
            output_ids = self.model.generate(**kwargs)
        #output_ids[0] :  응답값
        # [prompt_len:] : 입력값 이후. 모델의 응답만
        new_tokens = output_ids[0][prompt_len:]  #LLM의 답변 부분
        #decode : 문자열로 디코딩
        #skip_special_tokens=True : <|... 특수 토큰 제외
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    # 답변을 토큰 조각 단위로 하나씩 반환 (SSE 스트리밍용)
    def stream (
       self,
       messages : list[ChatMessage],
       max_new_tokens : int | None = None,
       temperature : float | None = None
    ) -> Iterator[str] :
        kwargs = self._generation_kwargs(messages,max_new_tokens,temperature)
        # skip_prompt=True : 프롬프트 부분은 제외하고 새로 생성된 텍스트만 전달
        #TextIteratorStreamer : 생성된 토큰을 문자열로 변경하여 큐에 저장하는 도구
        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        # 클라이언트가 연결을 끊으면 stop_event를 설정 → 생성 중단
        stop_event = threading.Event() #스레드가 실행되는 시점을 서로 통신
        kwargs["streamer"] = streamer
        # 토큰 생성시 조건을 검사해서 True인 경우 멈춤
        kwargs["stopping_criteria"] = StoppingCriteriaList([_StopOnEvent(stop_event)])

        # model.generate()는 끝날 때까지 블로킹되므로 별도 스레드에서 실행하고
        # 현재 스레드는 streamer에서 생성된 조각을 꺼내서 바로 반환
        def _run() :
            with self._lock, torch.inference_mode() :
                self.model.generate(**kwargs)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        try :
            for piece in streamer :
                if piece :
                    yield piece  #LLM의 응답메세지
        finally :
            # 정상 종료 / 연결 끊김(GeneratorExit) 모두 생성 스레드를 멈춤
            stop_event.set() #True로 설정
            thread.join() #스레드 종료

# stop_event가 설정되면 True를 반환하여 generate()를 중단시킴
class _StopOnEvent(StoppingCriteria) :
    def __init__(self, event : threading.Event) :
        self.event = event
    def __call__(self, input_ids, scores, **kwargs) -> bool :
        return self.event.is_set()

llm = QwenLLM(settings.model_id)