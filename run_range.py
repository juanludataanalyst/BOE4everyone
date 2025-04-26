import subprocess
import sys
from datetime import datetime, timedelta

start = datetime(2025, 4, 1)
end = datetime(2025, 4, 24)

python_exe = sys.executable  # Esto apunta SIEMPRE al python del venv activo

current = start
while current <= end:
    date_str = current.strftime("%Y-%m-%d")  # o "%Y%m%d" según acepte tu main.py
    print(f"Procesando {date_str}")
    subprocess.run([python_exe, "./src/main.py", "--date", date_str])
    current += timedelta(days=1)