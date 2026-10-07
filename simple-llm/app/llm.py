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

class QwenLLM :
    def __init__(self,model_id:str) :
        self.model_id = model_id
        self.okenizer =None
        self.model = None
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
        dtype = "auto" if use_cuda else torch.float32
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            dtype=dtype,
            device_map="auto" if use_cuda else "cpu"
        )
        self.model.eval()
        



llm = QwenLLM(settings.model_id)