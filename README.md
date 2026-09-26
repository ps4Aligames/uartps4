# UART Ali Games Edition

Professional USB-TTL/UART monitor for Windows.

## Included
- Auto-detect and auto-connect USB-TTL COM ports.
- Default baud 115200.
- Dark professional UI with gold AliGamer logo.
- Live UART log with INFO/WARNING/ERROR highlighting.
- Automatic web search when a UART error is detected.
- Web results displayed inside the app.
- Only web action button: **COPY WEB SOLUTION**.
- Clear Log and Save Log.
- EXE icon uses the gold AliGamer logo.

## GitHub Actions
Upload this project to GitHub, then run **Actions → Build UART Ali Games Edition**. The workflow produces `UART_Ali_Games_Edition.exe` as an artifact.

## Local build
```powershell
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --name UART_Ali_Games_Edition --icon assets/AliGamer.ico --add-data "assets;assets" src/uart_ali_games.py
```
