import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from uart_ali_games import App
import tkinter as tk
from PIL import ImageGrab

root=tk.Tk(); app=App(root)
logs=[
    'INFO USB-TTL terdeteksi di COM5','INFO Baud rate: 115200','INFO Koneksi UART berhasil','INFO Menunggu data...',
    'INFO < RX: 0x10 0x20 0x30 0x40','INFO < RX: OK','WARNING Tegangan tidak stabil: 4.8V',
    'INFO < RX: 0xAA 0x55 0x12 0x34','ERROR < RX: 0xFF 0x00 0x00 0x00','ERROR ERROR: UART Timeout',
    'INFO Mencari solusi di web...','INFO Pencarian web selesai. 4 hasil ditemukan.','INFO < RX: 0x10 0x20 0x30 0x40'
]
# Fill only the visual preview; actual app uses the same widgets and connection logic.
for x in logs:
    low=x.lower(); tag='error' if 'error' in low or 'timeout' in low else ('warn' if 'warning' in low else 'info')
    stamp='14:22:15.673'
    app.log.insert('end', f'[{stamp}]  {x}\n', tag)
app.log.see('end')
app.err_text.config(text='UART Timeout (0xFF 0x00 0x00 0x00)')
app.diag_text.config(text='✓  Periksa TX / RX / GND dan kabel USB-TTL.\n✓  Pastikan baud rate sesuai perangkat.\n✓  Periksa power, reset, dan respons target.\n✓  Pastikan driver USB-TTL terpasang.')
app.set_status('●  CONNECTED','#18e88b','COM5   |   115200 bps')
app.set_connected_box(True,'COM5 - Connected')
app.footer_msg.config(text='USB-TTL terdeteksi di COM5. Auto-connect berhasil.')
rows=[
('PS4 UART Timeout Error – Cara Mengatasi dan Solusi Lengkap','PSX-Place','https://www.psx-place.com/'),
('PS4 UART Error Fix – Common Issues and Solutions','Reddit','https://www.reddit.com/'),
('uart-ps4-fix – Troubleshooting Guide','GitHub','https://github.com/'),
('PS4 HEN – UART Connection Problem','Forum PSX-Scene','https://www.psx-scene.com/')]
app.show_results(rows)

def cap():
    root.update(); x=root.winfo_rootx(); y=root.winfo_rooty(); w=root.winfo_width(); h=root.winfo_height()
    base=Path(__file__).parent
    ImageGrab.grab(bbox=(x,y,x+w,y+h)).save(base/'preview_final.png')
    app.set_disconnected_state('Menunggu perangkat USB-TTL...')
    root.update(); ImageGrab.grab(bbox=(x,y,x+w,y+h)).save(base/'preview_waiting.png')
    root.destroy()
root.after(1000,cap); root.mainloop()
