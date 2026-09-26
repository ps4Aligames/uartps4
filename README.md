# UART Ali Games Edition

Versi final **AUTO USB-TTL** untuk Windows.

## Fitur
- UI dark professional 1240×780 dengan logo Ali Games gold.
- **AUTO DETECT** USB-TTL/COM.
- **AUTO CONNECT** saat USB-TTL terpasang.
- Indikator koneksi benar-benar mengikuti kondisi port:
  - 🟡 `USB-TTL Menunggu` = belum terhubung.
  - 🟢 `USB-TTL Terdeteksi` / `CONNECTED` = COM berhasil dibuka.
  - 🔴 `DETECTED / OPEN FAILED` = perangkat terlihat tetapi COM gagal dibuka.
  - Saat USB-TTL dicabut, status kembali otomatis ke waiting dan COM ditutup.
- Default baud `115200`, dengan pilihan baud umum.
- UART log dengan warna INFO/WARNING/ERROR.
- Error UART memicu **ERROR ANALYZER** dan pencarian web otomatis.
- Hasil pencarian web tampil di dalam aplikasi.
- Tombol web hanya **COPY WEB SOLUTION**.
- `Clear Log` dan `Save Log`.
- Icon EXE menggunakan logo Ali Games gold.

## Build di GitHub
1. Upload seluruh isi folder ini ke repository GitHub.
2. Buka **Actions**.
3. Pilih **Build UART Ali Games Edition**.
4. Jalankan workflow dengan **Run workflow** atau push ke `main`/`master`.
5. Download artifact `UART-Ali-Games-Edition`.

## Build lokal Windows PowerShell
```powershell
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --name 'UART_Ali_Games_Edition' --icon 'assets/AliGames.ico' --add-data 'assets;assets' src/uart_ali_games.py
```

EXE hasil build:
`dist\UART_Ali_Games_Edition.exe`

## Logo
Logo header dan icon EXE menggunakan logo **Ali Games** dari referensi pengguna, dengan tulisan **service** dihapus dan warna dibuat gold transparan. Tidak menggunakan logo AliGamer.
