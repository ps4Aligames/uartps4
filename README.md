# UART Ali Games Edition — FINAL COMPACT WAITING FIX

Versi final UI/USB-TTL dengan perubahan terakhir:
- Ukuran default window: 1040x640 (minimum 900x560).
- UART LOG tetap panjang dan `UART LOG` + `Auto Scroll` sejajar.
- Area COM Port tetap compact.
- `Clear Log` dan `Save Log` tetap tersedia.
- ERROR ANALYZER tetap tampil.
- WEB SOLUTIONS + `COPY WEB SOLUTION` tetap.
- Logo memakai `AliGames_logo_gold.png` transparan yang telah disetujui.
- Status USB-TTL: hijau hanya setelah serial berhasil dibuka; saat menunggu, box memakai warna dark-navy yang konsisten dengan tema, dengan indikator kuning.
- Auto-detect/auto-connect dan disconnect monitor tetap aktif.

Build:
`powershell -ExecutionPolicy Bypass -File build.ps1`
