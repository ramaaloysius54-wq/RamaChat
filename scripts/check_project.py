import py_compile
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def verify_project() -> bool:
    for py_file in BASE_DIR.rglob("*.py"):
        py_compile.compile(str(py_file), doraise=True)
    print("[OK] Semua file Python di RamaChat valid dan bebas syntax error.")
    return True

if __name__ == "__main__":
    sys.exit(0 if verify_project() else 1)
