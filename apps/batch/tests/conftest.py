# why: pytest 실행 환경에서 패키지 경로를 확실히 잡아 import 오류를 방지하기 위한 설정
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
