# BW&E UART Reader v2

Windows UART/COM reader with realtime log, error analyzer, web search and solution links.

## Build locally
```powershell
pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --name BW&E_UART_Reader_v2 src/bwe_uart_reader.py
```

## GitHub
Upload this folder to a repository. GitHub Actions will build the portable EXE automatically under **Actions > Build BW&E UART Reader v2 > Artifacts**.
