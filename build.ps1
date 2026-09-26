python -m pip install --upgrade pip pyinstaller pyserial Pillow requests
pyinstaller --noconfirm --clean --onefile --windowed --name 'UART_Ali_Games_Edition' --icon 'assets/AliGames.ico' --add-data 'assets;assets' src/uart_ali_games.py
Write-Host 'EXE: dist\UART_Ali_Games_Edition.exe'
