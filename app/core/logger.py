import logging
from pathlib import Path

_LOG_ROOT = Path(__file__).parents[2] / "logs"

_FORMATTER = logging.Formatter(
    "[%(asctime)s] [%(module)s] [%(levelname)s] %(message)s",
    "%Y-%m-%d %H:%M:%S",
)

def setup_logging() -> None:
    """애플리케이션 시작 시 한 번만 호출한다.

    root logger에 handler를 붙여, 각 모듈에서 logging.getLogger(__name__)로 얻은
    logger가 별도 설정 없이 이 handler들을 통해 출력되게 한다 (propagation).
    """
    _LOG_ROOT.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # INFO 레벨은 console에 출력
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_FORMATTER)

    # DEBUG 레벨은 debug.log에 저장
    debug_handler = logging.FileHandler(_LOG_ROOT / "debug.log", encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(_FORMATTER)

    # ERROR 레벨은 error.log에 저장
    error_handler = logging.FileHandler(_LOG_ROOT / "error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(_FORMATTER)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(debug_handler)
    root_logger.addHandler(error_handler)
