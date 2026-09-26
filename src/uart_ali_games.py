import os, sys, re, time, queue, threading, webbrowser, urllib.parse, html
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None

APP_TITLE = 'UART Ali Games Edition'
BG = '#05090f'; HEADER = '#070b11'; PANEL = '#0b121b'; PANEL2 = '#0f1925'; PANEL3 = '#081019'
BORDER = '#26384b'; GOLD = '#f2bf45'; GOLD2 = '#ffd96a'; CYAN = '#19c8ff'; GREEN = '#16e78a'; RED = '#ff3347'; YELLOW = '#ffd21c'; TEXT = '#eef5fb'; MUTED = '#8fa2b5'


def asset_path(name):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, 'assets', name)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry('1080x650')
        self.root.minsize(900, 560)
        self.root.configure(bg=BG)
        try: self.root.iconbitmap(asset_path('AliGames.ico'))
        except Exception: pass
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.ser = None; self.running = False; self.current_port = None
        self.connection_token = 0
        self.last_port_names = set()
        self.known_ports = set(); self.q = queue.Queue(); self.search_rows = []; self.selected_web = 0; self.last_error_key = None; self.last_error_time = 0
        self.logo_img = None; self.cards = []
        self.build_styles(); self.build_ui()
        self.set_disconnected_state('Menunggu perangkat USB-TTL...')
        self.refresh_ports(auto=True)
        self.root.after(100, self.drain_queue)
        self.root.after(1000, self.auto_monitor_ports)

    def build_styles(self):
        s = ttk.Style()
        try: s.theme_use('clam')
        except Exception: pass
        s.configure('.', background=BG, foreground=TEXT, font=('Segoe UI', 10))
        s.configure('TCombobox', fieldbackground=PANEL2, background=PANEL2, foreground=TEXT, arrowcolor=GOLD, bordercolor=BORDER)
        s.map('TCombobox', fieldbackground=[('readonly', PANEL2)], foreground=[('readonly', TEXT)])
        s.configure('Dark.TButton', background=PANEL2, foreground=TEXT, bordercolor=BORDER, padding=(14, 8), font=('Segoe UI', 9, 'bold'))
        s.map('Dark.TButton', background=[('active', '#17283b')], foreground=[('active', 'white')])
        s.configure('Gold.TButton', background=GOLD, foreground='#111', bordercolor=GOLD2, padding=(18, 10), font=('Segoe UI', 9, 'bold'))
        s.map('Gold.TButton', background=[('active', GOLD2)])

    def build_ui(self):
        self.build_header()
        self.build_connection()
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill='both', expand=True, padx=12, pady=(0, 10))
        body.grid_columnconfigure(0, weight=3, uniform='cols'); body.grid_columnconfigure(1, weight=2, uniform='cols')
        body.grid_rowconfigure(0, weight=1, minsize=295); body.grid_rowconfigure(1, weight=0, minsize=125); body.grid_rowconfigure(2, weight=0, minsize=34)
        self.build_uart_log(body, 0, 0)
        self.build_web(body, 0, 1, rowspan=2)
        self.build_analyzer(body, 1, 0)
        self.build_footer(body, 2, 0, colspan=2)

    def build_header(self):
        h = tk.Frame(self.root, bg=HEADER, height=100, highlightthickness=1, highlightbackground='#1b2b3a')
        h.pack(fill='x'); h.pack_propagate(False)
        tk.Frame(h, bg=GOLD, height=2).place(relx=0, rely=1, relwidth=1, anchor='sw')
        h.grid_columnconfigure(0, weight=0, minsize=215)
        h.grid_columnconfigure(1, weight=1, minsize=320)
        h.grid_columnconfigure(2, weight=0, minsize=185)
        if Image and ImageTk:
            try:
                im = Image.open(asset_path('AliGames_logo_gold.png')).convert('RGBA')
                im.thumbnail((205, 70), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(im)
                tk.Label(h, image=self.logo_img, bg=HEADER).grid(row=0,column=0,sticky='w',padx=(20,6),pady=10)
            except Exception:
                pass
        title = tk.Frame(h, bg=HEADER)
        title.grid(row=0,column=1,sticky='nsew',padx=4,pady=17)
        title.grid_columnconfigure(0, weight=1)
        title_row=tk.Frame(title,bg=HEADER); title_row.pack(anchor='w')
        tk.Label(title_row, text='UART ', bg=HEADER, fg=TEXT, font=('Segoe UI', 19, 'bold')).pack(side='left')
        tk.Label(title_row, text='Ali Games Edition', bg=HEADER, fg=GOLD2, font=('Segoe UI', 19, 'bold')).pack(side='left')
        tk.Label(title, text='AUTO DETECT   •   AUTO CONNECT   •   ERROR ANALYZER   •   WEB SOLUTIONS', bg=HEADER, fg=MUTED, font=('Segoe UI', 8, 'bold'), wraplength=360, justify='left').pack(anchor='w',pady=(3,0))
        right = tk.Frame(h, bg=HEADER); right.grid(row=0,column=2,sticky='e',padx=14,pady=18)
        tk.Label(right, text='USB-TTL', bg=HEADER, fg=TEXT, font=('Segoe UI', 9, 'bold')).pack(anchor='e')
        self.status = tk.Label(right, text='●  WAITING FOR USB-TTL', bg=HEADER, fg=YELLOW, font=('Segoe UI', 9, 'bold'))
        self.status.pack(anchor='e', pady=(4,0))
        self.status_detail = tk.Label(right, text='COM —  |  115200 bps', bg=HEADER, fg=MUTED, font=('Segoe UI', 8))
        self.status_detail.pack(anchor='e', pady=(2,0))

    def card(self, parent, row, col, rowspan=1, colspan=1):
        f = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        f.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, sticky='nsew', padx=5, pady=5)
        return f

    def heading(self, parent, text, color=GOLD2):
        bar = tk.Frame(parent, bg=PANEL, height=42); bar.pack(fill='x'); bar.pack_propagate(False)
        tk.Label(bar, text=text, bg=PANEL, fg=color, font=('Segoe UI', 12, 'bold')).pack(side='left', padx=14, pady=8)
        return bar

    def build_connection(self):
        c = tk.Frame(self.root, bg=PANEL, height=78, highlightthickness=1, highlightbackground=BORDER)
        c.pack(fill='x', padx=12, pady=(10, 8)); c.pack_propagate(False)

        # Rapikan blok koneksi: COM, baud, status USB-TTL, dan tombol dibuat seimbang.
        c.grid_columnconfigure(0, weight=0, minsize=170)
        c.grid_columnconfigure(1, weight=0, minsize=125)
        c.grid_columnconfigure(2, weight=1, minsize=240)
        c.grid_columnconfigure(3, weight=0, minsize=220)

        # COM PORT (AUTO DETECT) - tetap compact, hanya menampilkan COMx.
        left = tk.Frame(c, bg=PANEL)
        left.grid(row=0, column=0, sticky='nsew', padx=(14, 6), pady=10)
        tk.Label(left, text='COM PORT  (AUTO DETECT)', bg=PANEL, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w')
        row = tk.Frame(left, bg=PANEL, height=32)
        row.pack(fill='x', pady=(5, 0)); row.pack_propagate(False)
        self.port = ttk.Combobox(row, width=7, state='readonly')
        self.port.pack(side='left', fill='both', expand=True)
        ttk.Button(row, text='↻', width=3, style='Dark.TButton',
                   command=lambda: self.refresh_ports(auto=True)).pack(side='left', padx=(4, 0), fill='y')

        # BAUD RATE - tinggi field diseragamkan dengan selector COM.
        mid = tk.Frame(c, bg=PANEL)
        mid.grid(row=0, column=1, sticky='nsew', padx=6, pady=10)
        tk.Label(mid, text='BAUD RATE', bg=PANEL, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w')
        self.baud = ttk.Combobox(mid, width=8,
                                 values=['9600','19200','38400','57600','115200','230400','460800','921600'],
                                 state='readonly')
        self.baud.set('115200')
        self.baud.pack(fill='x', ipady=3, pady=(5, 0))

        # USB-TTL STATUS - dibuat proporsional terhadap blok COM/baud dan tombol.
        self.conn_box = tk.Frame(c, bg='#15100a', highlightthickness=1,
                                 highlightbackground='#6f5819', height=50)
        self.conn_box.grid(row=0, column=2, sticky='ew', padx=8, pady=13)
        self.conn_box.grid_propagate(False)
        self.conn_dot = tk.Label(self.conn_box, text='●', bg='#15100a', fg=YELLOW,
                                 font=('Segoe UI', 15))
        self.conn_dot.pack(side='left', padx=(12, 4))
        tx = tk.Frame(self.conn_box, bg='#15100a')
        tx.pack(side='left', fill='both', expand=True, pady=6)
        self.conn_title = tk.Label(tx, text='USB-TTL Menunggu', bg='#15100a', fg=YELLOW,
                                   font=('Segoe UI', 9, 'bold'))
        self.conn_title.pack(anchor='w')
        self.conn_detail = tk.Label(tx, text='Colokkan perangkat...', bg='#15100a', fg=TEXT,
                                    font=('Segoe UI', 8))
        self.conn_detail.pack(anchor='w', pady=(1, 0))

        # Tombol LOG wajib tetap tampil di kanan: Clear Log + Save Log.
        # Hanya area tombol ini yang ditegaskan; layout panel lain tidak diubah.
        btns = tk.Frame(c, bg=PANEL, width=214, height=50)
        btns.grid(row=0, column=3, sticky='e', padx=(4, 12), pady=13)
        btns.grid_propagate(False)
        btns.grid_columnconfigure(0, weight=1, uniform='logbtn')
        btns.grid_columnconfigure(1, weight=1, uniform='logbtn')
        btns.grid_rowconfigure(0, weight=1)
        ttk.Button(btns, text='Clear Log', style='Dark.TButton', command=self.clear_log).grid(row=0, column=0, sticky='nsew', padx=(0, 4))
        ttk.Button(btns, text='Save Log', style='Gold.TButton', command=self.save_log).grid(row=0, column=1, sticky='nsew', padx=(4, 0))

    def build_uart_log(self, parent, r, c):
        f=self.card(parent,r,c)
        # Header UART LOG + Auto Scroll berada pada satu baris agar tinggi terminal maksimal.
        top=tk.Frame(f,bg=PANEL,height=36)
        top.pack(fill='x',padx=12,pady=(0,3))
        top.pack_propagate(False)
        tk.Label(top, text='▣  UART LOG', bg=PANEL, fg=CYAN,
                 font=('Segoe UI', 12, 'bold')).pack(side='left', padx=(2,0), pady=6)
        self.autoscroll=tk.BooleanVar(value=True)
        tk.Checkbutton(top,text='Auto Scroll',variable=self.autoscroll,bg=PANEL,fg=TEXT,
                       selectcolor=PANEL2,activebackground=PANEL,activeforeground=TEXT,
                       font=('Segoe UI', 9)).pack(side='right', pady=4)
        wrap=tk.Frame(f,bg='#03070b'); wrap.pack(fill='both',expand=True,padx=10,pady=(0,8))
        # UART LOG memakai hampir seluruh tinggi panel; header dibuat satu baris agar ruang terminal maksimal.
        self.log=tk.Text(wrap,bg='#03070b',fg='#dbe8f2',insertbackground=CYAN,selectbackground='#183247',relief='flat',font=('Consolas',9),wrap='none',width=1,height=1,padx=10,pady=8)
        self.log.tag_configure('error',foreground=RED); self.log.tag_configure('warn',foreground=YELLOW); self.log.tag_configure('info',foreground=CYAN); self.log.tag_configure('normal',foreground=TEXT)
        sy=ttk.Scrollbar(wrap,orient='vertical',command=self.log.yview); sx=ttk.Scrollbar(wrap,orient='horizontal',command=self.log.xview); self.log.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        self.log.pack(side='left',fill='both',expand=True); sy.pack(side='right',fill='y'); sx.pack(side='bottom',fill='x')

    def build_web(self,parent,r,c,rowspan=1):
        f=self.card(parent,r,c,rowspan=rowspan)
        f.grid_rowconfigure(2, weight=1)
        f.grid_columnconfigure(0, weight=1)
        self.heading(f,'◉  WEB SOLUTIONS',GOLD2).grid(row=0,column=0,columnspan=2,sticky='ew')
        self.web_status=tk.Label(f,text='Menunggu error...',bg=PANEL,fg=MUTED,font=('Segoe UI',8,'bold'))
        self.web_status.grid(row=1,column=0,columnspan=2,sticky='e',padx=14,pady=(0,5))
        canvas_wrap=tk.Frame(f,bg=PANEL)
        canvas_wrap.grid(row=2,column=0,columnspan=2,sticky='nsew',padx=10,pady=(0,8))
        canvas_wrap.grid_rowconfigure(0,weight=1); canvas_wrap.grid_columnconfigure(0,weight=1)
        self.web_canvas=tk.Canvas(canvas_wrap,bg=PANEL,highlightthickness=0,width=1,height=1)
        sb=ttk.Scrollbar(canvas_wrap,orient='vertical',command=self.web_canvas.yview)
        self.web_canvas.configure(yscrollcommand=sb.set)
        self.web_inner=tk.Frame(self.web_canvas,bg=PANEL)
        self.web_window_id=self.web_canvas.create_window((0,0),window=self.web_inner,anchor='nw')
        self.web_inner.bind('<Configure>',lambda e:self.web_canvas.configure(scrollregion=self.web_canvas.bbox('all')))
        self.web_canvas.bind('<Configure>',lambda e:self.web_canvas.itemconfigure(self.web_window_id,width=max(1,e.width)))
        self.web_canvas.grid(row=0,column=0,sticky='nsew'); sb.grid(row=0,column=1,sticky='ns')
        bottom=tk.Frame(f,bg=PANEL)
        bottom.grid(row=3,column=0,columnspan=2,sticky='ew',padx=10,pady=(0,10))
        bottom.grid_columnconfigure(0,weight=1)
        ttk.Button(bottom,text='COPY WEB SOLUTION',style='Gold.TButton',command=self.copy_web_solution).grid(row=0,column=0,sticky='ew')
        self.render_web_placeholder()

    def render_web_placeholder(self):
        for w in self.web_inner.winfo_children(): w.destroy()
        tk.Label(self.web_inner,text='Hasil pencarian error akan muncul otomatis di sini.',bg=PANEL,fg=MUTED,font=('Segoe UI',9),wraplength=260,justify='center').pack(fill='x',padx=12,pady=30)

    def build_analyzer(self,parent,r,c):
        f=self.card(parent,r,c); self.heading(f,'⌕  ERROR ANALYZER',GOLD2)
        inner=tk.Frame(f,bg=PANEL); inner.pack(fill='both',expand=True,padx=10,pady=4)
        self.err_box=tk.Frame(inner,bg='#16080b',highlightthickness=1,highlightbackground=RED); self.err_box.pack(side='left',fill='both',expand=True,padx=(0,6))
        tk.Label(self.err_box,text='⚠  Error Detected',bg='#16080b',fg=RED,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=10,pady=(6,2))
        self.err_text=tk.Label(self.err_box,text='Belum ada error terdeteksi.',bg='#16080b',fg=TEXT,font=('Segoe UI',8),justify='left',wraplength=210); self.err_text.pack(anchor='w',padx=10,pady=(0,6))
        self.diag=tk.Frame(inner,bg=PANEL2,highlightthickness=1,highlightbackground='#6f5819'); self.diag.pack(side='left',fill='both',expand=True,padx=(6,0))
        tk.Label(self.diag,text='💡  Diagnosis & Solusi',bg=PANEL2,fg=GOLD2,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=10,pady=(6,2))
        self.diag_text=tk.Label(self.diag,text='Pencarian solusi web akan berjalan otomatis saat error UART terdeteksi.',bg=PANEL2,fg=TEXT,font=('Segoe UI',8),justify='left',wraplength=230); self.diag_text.pack(anchor='w',padx=10,pady=(0,6))

    def build_footer(self,parent,r,c,colspan=1):
        f=tk.Frame(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER,height=44)
        f.grid(row=r,column=c,columnspan=colspan,sticky='ew',padx=5,pady=5)
        f.grid_propagate(False)
        self.footer_msg=tk.Label(f,text='USB-TTL belum terhubung. Colokkan perangkat untuk auto-connect.',bg=PANEL,fg=MUTED,font=('Segoe UI',8,'bold'),anchor='w',wraplength=380,justify='left')
        self.footer_msg.pack(side='left',fill='x',expand=True,padx=14)
        tk.Label(f,text='Web search: automatic   |   COPY WEB SOLUTION',bg=PANEL,fg=GOLD2,font=('Segoe UI',8,'bold'),anchor='e').pack(side='right',padx=14)

    def _port_is_usb_serial(self, p):
        text = ' '.join(str(x or '') for x in (p.description, p.manufacturer, p.product, p.hwid)).lower()
        keys = ('usb', 'ttl', 'serial', 'ch340', 'ch341', 'cp210', 'ftdi', 'silicon labs', 'prolific')
        return any(k in text for k in keys)

    def refresh_ports(self,auto=False):
        ports=[] if list_ports is None else list(list_ports.comports())
        vals=[p.device for p in ports]
        self.port['values']=vals
        if self.current_port and any(p.device == self.current_port for p in ports):
            idx=next(i for i,p in enumerate(ports) if p.device == self.current_port)
            self.port.current(idx)
        elif vals and not self.port.get():
            self.port.current(0)
        if auto and ports and not self.running:
            candidates=[p for p in ports if self._port_is_usb_serial(p)] or ports
            chosen=candidates[0]
            self.port.set(chosen.device)
            self.connect(chosen.device)

    def auto_monitor_ports(self):
        try:
            ports=[] if list_ports is None else list(list_ports.comports())
            names={p.device for p in ports}
            added=names - self.last_port_names
            removed=self.last_port_names - names
            self.last_port_names=names
            vals=[p.device for p in ports]
            self.port['values']=vals
            if self.running and self.current_port and self.current_port not in names:
                old=self.current_port
                self.append_log(f'WARNING USB-TTL disconnected: {old}')
                self.disconnect(log=False)
            if not self.running and ports and (added or not self.current_port):
                candidates=[p for p in ports if p.device in added and self._port_is_usb_serial(p)]
                if not candidates: candidates=[p for p in ports if p.device in added] or [p for p in ports if self._port_is_usb_serial(p)] or ports
                chosen=candidates[0]
                for i,p in enumerate(ports):
                    if p.device == chosen.device: self.port.current(i); break
                self.connect(chosen.device)
        except Exception:
            pass
        self.root.after(500,self.auto_monitor_ports)

    def connect(self,p):
        if serial is None:
            self.set_status('●  PYTHON SERIAL ERROR',RED,'pyserial tidak tersedia')
            self.set_connected_box(False, 'pyserial belum terpasang')
            return
        if self.running and self.current_port == p:
            return
        if self.running:
            self.disconnect(log=False)
        token=self.connection_token+1
        self.connection_token=token
        try:
            baud=int(self.baud.get())
            ser=serial.Serial(p,baud,timeout=0.25)
            self.ser=ser; self.running=True; self.current_port=p
            self.set_status('●  CONNECTED',GREEN,f'{p}  |  {baud} bps')
            self.set_connected_box(True, f'{p} - Connected')
            self.footer_msg.config(text=f'USB-TTL terdeteksi di {p}. Auto-connect berhasil.')
            self.append_log(f'INFO USB-TTL terdeteksi di {p}')
            self.append_log(f'INFO Baud rate: {baud}')
            threading.Thread(target=self.reader,args=(ser,token),daemon=True).start()
        except Exception as e:
            self.running=False; self.ser=None; self.current_port=None
            self.set_status('●  DETECTED / OPEN FAILED',RED,f'{p}')
            self.set_connected_box(False, f'{p} - gagal dibuka')
            self.footer_msg.config(text=f'USB-TTL terdeteksi di {p}, tetapi COM gagal dibuka.')
            self.append_log('ERROR COM open failed: '+str(e))

    def set_connected_box(self, connected, detail):
        if connected:
            bg='#071a14'; border='#0d7553'; fg=GREEN; title='USB-TTL Terdeteksi'
        else:
            bg='#15100a'; border='#6f5819'; fg=YELLOW; title='USB-TTL Menunggu'
        self.conn_box.config(bg=bg,highlightbackground=border)
        self.conn_dot.config(bg=bg,fg=fg)
        self.conn_title.config(bg=bg,fg=fg,text=title)
        self.conn_detail.config(bg=bg,text=detail)

    def set_disconnected_state(self, detail='Menunggu perangkat...'):
        self.set_status('●  WAITING FOR USB-TTL',YELLOW,'COM —  |  115200 bps')
        self.set_connected_box(False, detail)
        if hasattr(self,'footer_msg'):
            self.footer_msg.config(text='USB-TTL belum terhubung. Colokkan perangkat untuk auto-connect.')

    def disconnect(self, log=True):
        self.connection_token += 1
        self.running=False
        old=self.current_port
        try:
            if self.ser: self.ser.close()
        except Exception: pass
        self.ser=None; self.current_port=None
        self.set_disconnected_state()
        if log and old:
            self.append_log(f'WARNING USB-TTL disconnected: {old}')

    def set_status(self,text,color,detail):
        self.status.config(text=text,fg=color); self.status_detail.config(text=detail)

    def reader(self, ser, token):
        while self.running and self.ser is ser and self.connection_token == token:
            try:
                data=ser.readline()
                if data: self.q.put(data.decode('utf-8','replace').rstrip('\r\n'))
            except Exception as e:
                if self.connection_token == token:
                    self.q.put('ERROR UART read: '+str(e))
                break

    def drain_queue(self):
        while not self.q.empty(): self.append_log(self.q.get())
        self.root.after(100,self.drain_queue)

    def append_log(self,text):
        stamp=datetime.now().strftime('%H:%M:%S.%f')[:-3]
        low=text.lower()
        # Jangan menganggap data hex biasa (mis. 0xAA 0x55) sebagai error.
        iserr=bool(re.search(r'\b(error|failed|failure|timeout|exception|denied|fatal)\b',low)) or low.startswith('error:') or low.startswith('error |')
        iswarn=bool(re.search(r'\bwarning\b',low))
        tag='error' if iserr else ('warn' if iswarn else ('info' if 'info' in low else 'normal'))
        self.log.insert('end',f'[{stamp}]  {text}\n',tag)
        if self.autoscroll.get(): self.log.see('end')
        if iserr:
            self.root.after(50,lambda e=text:self.handle_error(e))

    def handle_error(self,error):
        error=error.strip()
        key=error.lower()
        now=time.time()
        self.err_text.config(text=error)
        self.diag_text.config(text=self.local_diagnosis(error))
        # Tampilkan error terakhir secara konsisten dan hindari web search berulang untuk baris identik.
        if key != self.last_error_key or now-self.last_error_time > 3:
            self.last_error_key=key; self.last_error_time=now
            self.search_web(error)

    def local_diagnosis(self,q):
        low=q.lower(); hints=[]
        if 'timeout' in low: hints += ['Periksa TX / RX / GND dan kabel USB-TTL.', 'Pastikan baud rate sesuai perangkat.', 'Periksa power, reset, dan respons target.']
        if 'permission' in low or 'access is denied' in low: hints += ['COM sedang dipakai aplikasi lain.', 'Tutup serial monitor lain.']
        if '0xffffffff' in low or 'invalid' in low or 'header' in low: hints += ['Periksa wiring dan level tegangan.', 'Pastikan target berada pada kondisi yang benar.']
        if 'com' in low or 'serial' in low: hints += ['Periksa driver USB-TTL dan COM Port.']
        if not hints: hints=['Tidak ada pola spesifik. Hasil web akan mencari dokumentasi terkait pesan error ini.']
        return '\n'.join('✓  '+x for x in dict.fromkeys(hints))

    def search_web(self,error):
        q=error.replace('\n',' ')[:500]
        if not q: return
        if not any(k in q.lower() for k in ('uart','serial','ps4','nor','usb')): q += ' UART USB TTL PS4'
        self.web_status.config(text='Mencari solusi...',fg=CYAN)
        threading.Thread(target=self.web_worker,args=(q,),daemon=True).start()

    def web_worker(self,q):
        rows=[]
        try:
            if requests is None: raise RuntimeError('requests belum terpasang')
            url='https://html.duckduckgo.com/html/?'+urllib.parse.urlencode({'q':q})
            r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=15); r.raise_for_status()
            blocks=re.findall(r'<a[^>]+class=["\']result__a["\'][^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',r.text,re.S|re.I)
            for href,title in blocks[:8]:
                title=html.unescape(re.sub('<.*?>','',title)).strip(); href=html.unescape(href)
                m=re.search(r'uddg=([^&]+)',href); href=urllib.parse.unquote(m.group(1)) if m else href
                source=urllib.parse.urlparse(href).netloc or 'Web'
                rows.append((title,source,href))
        except Exception as e:
            rows=[('Pencarian web gagal',str(e),'')]
        self.root.after(0,lambda:self.show_results(rows))

    def show_results(self,rows):
        self.search_rows=rows
        for w in self.web_inner.winfo_children(): w.destroy()
        for i,(title,source,href) in enumerate(rows):
            card=tk.Frame(self.web_inner,bg=PANEL2,highlightthickness=1,highlightbackground=(CYAN if i==0 else BORDER)); card.pack(fill='x',padx=5,pady=5)
            tk.Label(card,text=title,bg=PANEL2,fg=TEXT,font=('Segoe UI',10,'bold'),wraplength=260,justify='left').pack(anchor='w',padx=12,pady=(10,2))
            tk.Label(card,text=source,bg=PANEL2,fg=GOLD2,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=12)
            link=tk.Label(card,text=href,bg=PANEL2,fg=CYAN,font=('Segoe UI',8),cursor='hand2',wraplength=260,justify='left')
            link.pack(anchor='w',padx=12,pady=(2,10))
            if href: link.bind('<Button-1>',lambda e,u=href:webbrowser.open(u))
            card.bind('<Button-1>',lambda e,idx=i:self.select_web(idx))
            for child in card.winfo_children(): child.bind('<Button-1>',lambda e,idx=i:self.select_web(idx))
        self.web_status.config(text=f'{len(rows)} hasil ditemukan',fg=GREEN if rows and rows[0][0] != 'Pencarian web gagal' else RED)

    def select_web(self,i):
        if 0 <= i < len(self.search_rows): self.selected_web=i

    def copy_web_solution(self):
        if not self.search_rows: return
        i=getattr(self,'selected_web',0)
        i=max(0,min(i,len(self.search_rows)-1)); title,source,href=self.search_rows[i]
        text=f'{title}\nSource: {source}\nLink: {href}'
        self.root.clipboard_clear(); self.root.clipboard_append(text); self.root.update()
        self.footer_msg.config(text='Web solution berhasil disalin ke clipboard.')
        self.set_status('●  WEB SOLUTION COPIED',CYAN,self.current_port or 'COM —')

    def clear_log(self): self.log.delete('1.0','end')

    def save_log(self):
        p=filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Text','*.txt'),('All files','*.*')])
        if p:
            with open(p,'w',encoding='utf-8') as f: f.write(self.log.get('1.0','end'))

    def on_close(self):
        self.disconnect(); self.root.destroy()


if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
