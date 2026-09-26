# UART Ali Games Edition — FINAL COMPACT STATUS + BUTTON FIX

Versi final dengan UI compact dan status koneksi USB-TTL yang terlihat jelas.

## Perubahan terakhir
- Ukuran default window: **1040x660**.
- Ukuran minimum: **900x580**.
- **Clear Log** dan **Save Log** memakai tombol fixed-size agar tulisan tidak terpotong.
- Header status **USB-TTL / CONNECTED / COMx / baud** tetap terlihat pada ukuran compact.
- Box koneksi menampilkan **USB-TTL Terdeteksi** saat Serial berhasil dibuka.
- Saat tidak ada perangkat, box menampilkan **USB-TTL Menunggu** dengan warna dark-navy + indikator kuning.
- Saat USB-TTL dicabut, aplikasi mendeteksi perubahan port dan kembali ke WAITING.
- UART LOG tetap menjadi area utama dan `UART LOG` + `Auto Scroll` sejajar.
- COM Port tetap compact, misalnya `COM9`.
- ERROR ANALYZER tetap menampilkan **Error Detected** dan **Diagnosis & Solusi**.
- WEB SOLUTIONS + `COPY WEB SOLUTION` tetap.
- Logo memakai **AliGames_logo_gold.png** transparan yang disetujui.
- Icon EXE memakai **AliGames.ico** multi-resolution.

## Build GitHub Actions
Workflow: `.github/workflows/build-windows.yml`

## Build lokal
```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Output:
`dist\UART_Ali_Games_Edition.exe`
