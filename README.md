# UART Ali Games Edition

Windows desktop UART/USB-TTL diagnostic tool with a dark gold/cyan interface.

## Tampilan & fungsi
- Logo **Ali Games gold transparan** menggunakan artwork yang diberikan pengguna.
- USB-TTL **Auto Detect + Auto Connect** memakai `pyserial`.
- Indikator header dan connection box berubah hanya setelah port serial berhasil dibuka.
- Saat USB-TTL dicabut, koneksi ditutup dan status kembali **WAITING**.
- UART LOG panjang dengan Auto Scroll.
- ERROR ANALYZER menampilkan error terakhir dan diagnosis lokal.
- WEB SOLUTIONS mencari hasil web otomatis untuk error UART.
- Tombol **COPY WEB SOLUTION**, **Clear Log**, dan **Save Log**.
- COM selector dibuat compact agar cukup menampilkan `COM5`, `COM9`, dll.

## Build lokal
```powershell
./build.ps1
```
Hasil: `dist/UART_Ali_Games_Edition.exe`

## GitHub Actions
Upload seluruh folder project ke repository GitHub, lalu jalankan workflow **Build UART Ali Games Edition**.
