import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, queue, re, webbrowser, urllib.parse, time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

APP_TITLE = 'BW&E UART Reader v2'

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry('1100x720')
        self.root.minsize(900, 600)
        self.ser = None
        self.running = False
        self.q = queue.Queue()
        self.build_ui()
        self.refresh_ports()
        self.root.after(100, self.drain_queue)

    def build_ui(self):
        top = ttk.Frame(self.root, padding=10); top.pack(fill='x')
        ttk.Label(top, text='COM Port').pack(side='left')
        self.port = ttk.Combobox(top, width=14, state='readonly'); self.port.pack(side='left', padx=6)
        ttk.Button(top, text='Refresh', command=self.refresh_ports).pack(side='left')
        ttk.Label(top, text='Baud').pack(side='left', padx=(18,4))
        self.baud = ttk.Combobox(top, width=12, values=['9600','19200','38400','57600','115200','230400','460800','921600'], state='readonly')
        self.baud.set('115200'); self.baud.pack(side='left')
        self.connect_btn = ttk.Button(top, text='CONNECT', command=self.toggle_connection); self.connect_btn.pack(side='left', padx=10)
        ttk.Button(top, text='Clear', command=self.clear_log).pack(side='left')
        ttk.Button(top, text='Save Log', command=self.save_log).pack(side='left', padx=6)

        main = ttk.Panedwindow(self.root, orient='vertical'); main.pack(fill='both', expand=True, padx=10, pady=(0,10))
        log_frame = ttk.Labelframe(main, text='UART LOG', padding=6); main.add(log_frame, weight=4)
        self.log = tk.Text(log_frame, wrap='none', font=('Consolas',10), undo=False)
        sy = ttk.Scrollbar(log_frame, orient='vertical', command=self.log.yview); self.log.configure(yscrollcommand=sy.set)
        self.log.pack(side='left', fill='both', expand=True); sy.pack(side='right', fill='y')

        bottom = ttk.Frame(main, padding=6); main.add(bottom, weight=2)
        ttk.Label(bottom, text='ERROR / LOG ANALYZER').pack(anchor='w')
        self.query = tk.Text(bottom, height=5, font=('Consolas',10)); self.query.pack(fill='x', pady=5)
        btns = ttk.Frame(bottom); btns.pack(fill='x')
        ttk.Button(btns, text='ANALYZE', command=self.analyze).pack(side='left')
        ttk.Button(btns, text='SEARCH WEB', command=self.search_web).pack(side='left', padx=6)
        ttk.Button(btns, text='COPY ERROR', command=self.copy_error).pack(side='left')
        ttk.Button(btns, text='Open Search', command=self.open_search).pack(side='left', padx=6)
        self.status = ttk.Label(btns, text='Disconnected'); self.status.pack(side='right')
        self.results = tk.Text(bottom, height=8, wrap='word', font=('Segoe UI',10), state='disabled')
        self.results.pack(fill='both', expand=True, pady=(6,0))
        self.last_url = ''

    def refresh_ports(self):
        ports = [] if list_ports is None else [p.device for p in list_ports.comports()]
        self.port['values'] = ports
        if ports: self.port.current(0)

    def toggle_connection(self):
        if self.running: self.disconnect()
        else: self.connect()

    def connect(self):
        if serial is None:
            messagebox.showerror('Missing dependency', 'pyserial belum terpasang.')
            return
        p = self.port.get()
        if not p:
            messagebox.showwarning('UART', 'Pilih COM port terlebih dahulu.'); return
        try:
            self.ser = serial.Serial(p, int(self.baud.get()), timeout=0.2)
            self.running = True
            self.connect_btn.config(text='DISCONNECT')
            self.status.config(text=f'Connected: {p}')
            self.append_log(f'INFO Connected to {p} @ {self.baud.get()}')
            threading.Thread(target=self.reader, daemon=True).start()
        except Exception as e:
            self.append_log('ERROR ' + str(e))
            messagebox.showerror('Connection error', str(e))

    def disconnect(self):
        self.running = False
        try:
            if self.ser: self.ser.close()
        except Exception: pass
        self.ser = None
        self.connect_btn.config(text='CONNECT'); self.status.config(text='Disconnected')

    def reader(self):
        while self.running and self.ser:
            try:
                data = self.ser.readline()
                if data:
                    text = data.decode('utf-8','replace').rstrip('\r\n')
                    self.q.put(text)
            except Exception as e:
                self.q.put('ERROR ' + str(e)); break

    def drain_queue(self):
        while not self.q.empty(): self.append_log(self.q.get())
        self.root.after(100, self.drain_queue)

    def append_log(self, text):
        stamp = time.strftime('%H:%M:%S')
        self.log.insert('end', f'[{stamp}] {text}\n'); self.log.see('end')
        if re.search(r'error|fail|failed|timeout|invalid|exception|not found|denied|0x[0-9a-f]+', text, re.I):
            self.query.delete('1.0','end'); self.query.insert('1.0', text)

    def clear_log(self): self.log.delete('1.0','end')
    def get_error(self): return self.query.get('1.0','end').strip() or self.log.get('1.0','end').strip()[-4000:]
    def copy_error(self): self.root.clipboard_clear(); self.root.clipboard_append(self.get_error()); self.status.config(text='Error copied')

    def analyze(self):
        q = self.get_error(); low = q.lower()
        hints=[]
        if 'timeout' in low: hints += ['Periksa TX/RX/GND dan koneksi USB-UART.', 'Pastikan baud rate sesuai target.', 'Periksa power/reset dan apakah perangkat benar-benar mengirim respons.']
        if 'permission' in low or 'access is denied' in low: hints += ['Pastikan COM tidak sedang dipakai aplikasi lain.', 'Coba tutup terminal/serial monitor lain.']
        if 'invalid' in low or 'header' in low or '0xffffffff' in low: hints += ['Periksa wiring dan level tegangan.', 'Pastikan target NOR/chip dalam kondisi dan mode yang benar.', 'Bandingkan hasil pembacaan dengan dump yang diketahui valid.']
        if 'com' in low or 'serial' in low: hints += ['Coba COM port yang benar dan driver USB-UART yang sesuai.']
        if not hints: hints=['Belum ada pola spesifik. Cari pesan error lengkap agar diagnosis lebih akurat.']
        self.set_results('ANALISIS\n\n' + '\n'.join('• '+x for x in dict.fromkeys(hints)))

    def search_url(self):
        q=self.get_error().replace('\n',' ')[:500]
        terms=['UART','serial','PS4','NOR']
        if not any(t.lower() in q.lower() for t in terms): q += ' UART PS4 NOR'
        return 'https://www.google.com/search?' + urllib.parse.urlencode({'q':q})

    def search_web(self):
        self.last_url=self.search_url(); self.set_results('PENCARIAN WEB\n\nMencari:\n'+urllib.parse.unquote(self.last_url.split('q=',1)[-1]).replace('+',' ')+'\n\nKlik “Open Search” untuk melihat hasil HTML dan sumber solusi di browser.')
        webbrowser.open(self.last_url)

    def open_search(self):
        if not self.last_url: self.search_web()
        else: webbrowser.open(self.last_url)

    def set_results(self, text):
        self.results.config(state='normal'); self.results.delete('1.0','end'); self.results.insert('1.0',text); self.results.config(state='disabled')

    def save_log(self):
        p=filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text','*.txt'),('All','*.*')])
        if p:
            with open(p,'w',encoding='utf-8') as f: f.write(self.log.get('1.0','end'))
            self.status.config(text='Log saved')

if __name__ == '__main__':
    root=tk.Tk(); App(root); root.mainloop()
