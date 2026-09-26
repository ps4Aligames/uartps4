import os, sys, re, time, queue, threading, webbrowser, urllib.parse, html
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog

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
BG = '#05090f'
HEADER = '#070c13'
PANEL = '#09121c'
PANEL2 = '#101c2a'
PANEL3 = '#040a10'
BORDER = '#26394e'
BORDER2 = '#1a2b3d'
GOLD = '#f2bd42'
GOLD2 = '#ffd96b'
CYAN = '#12c8ff'
GREEN = '#18e88b'
RED = '#ff3448'
YELLOW = '#ffd21f'
TEXT = '#edf5ff'
MUTED = '#91a5ba'


def asset_path(name):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, 'assets', name)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry('1040x660')
        self.root.minsize(900, 580)
        self.root.configure(bg=BG)
        try:
            self.root.iconbitmap(asset_path('AliGames.ico'))
        except Exception:
            pass
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        self.ser = None
        self.running = False
        self.current_port = None
        self.connection_token = 0
        self.last_port_names = set()
        self.q = queue.Queue()
        self.search_rows = []
        self.selected_web = 0
        self.last_error_key = None
        self.last_error_time = 0
        self.logo_img = None

        self.build_styles()
        self.build_ui()
        self.set_disconnected_state('Menunggu perangkat USB-TTL...')
        self.refresh_ports(auto=True)
        self.root.after(100, self.drain_queue)
        self.root.after(500, self.auto_monitor_ports)

    def build_styles(self):
        s = ttk.Style()
        try:
            s.theme_use('clam')
        except Exception:
            pass
        s.configure('.', background=BG, foreground=TEXT, font=('Segoe UI', 10))
        s.configure('TCombobox',
                    fieldbackground=PANEL2, background=PANEL2,
                    foreground=TEXT, arrowcolor=GOLD2,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        s.map('TCombobox', fieldbackground=[('readonly', PANEL2)], foreground=[('readonly', TEXT)])
        s.configure('Dark.TButton', background=PANEL2, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    padding=(16, 9), font=('Segoe UI', 10, 'bold'))
        s.map('Dark.TButton', background=[('active', '#17283b')], foreground=[('active', '#ffffff')])
        s.configure('Gold.TButton', background=GOLD, foreground='#11151a',
                    bordercolor=GOLD2, lightcolor=GOLD2, darkcolor=GOLD,
                    padding=(18, 10), font=('Segoe UI', 10, 'bold'))
        s.map('Gold.TButton', background=[('active', GOLD2)])

    def build_ui(self):
        self.build_header()
        self.build_connection()

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill='both', expand=True, padx=14, pady=(0, 12))
        body.grid_columnconfigure(0, weight=3, uniform='maincols', minsize=620)
        body.grid_columnconfigure(1, weight=2, uniform='maincols', minsize=360)
        body.grid_rowconfigure(0, weight=6, minsize=255)
        body.grid_rowconfigure(1, weight=0, minsize=150)
        body.grid_rowconfigure(2, weight=0, minsize=30)

        self.build_uart_log(body, 0, 0)
        self.build_web(body, 0, 1, rowspan=2)
        self.build_analyzer(body, 1, 0)
        self.build_footer(body, 2, 0, colspan=2)

    def build_header(self):
        h = tk.Frame(self.root, bg=HEADER, height=115,
                     highlightthickness=1, highlightbackground='#1b2b3b')
        h.pack(fill='x')
        h.pack_propagate(False)
        tk.Frame(h, bg=GOLD, height=2).place(relx=0, rely=1, relwidth=1, anchor='sw')

        h.grid_columnconfigure(0, weight=0, minsize=235)
        h.grid_columnconfigure(1, weight=1, minsize=435)
        h.grid_columnconfigure(2, weight=0, minsize=235)

        # The supplied Ali Games logo is used directly; no redraw or replacement.
        if Image and ImageTk:
            try:
                im = Image.open(asset_path('AliGames_logo_gold.png')).convert('RGBA')
                im.thumbnail((205, 82), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(im)
                tk.Label(h, image=self.logo_img, bg=HEADER, bd=0).grid(
                    row=0, column=0, sticky='w', padx=(28, 4), pady=10)
            except Exception:
                pass

        title = tk.Frame(h, bg=HEADER)
        title.grid(row=0, column=1, sticky='nsew', padx=(6, 4), pady=(23, 16))
        title_row = tk.Frame(title, bg=HEADER)
        title_row.pack(anchor='w')
        tk.Label(title_row, text='UART ', bg=HEADER, fg=TEXT,
                 font=('Segoe UI', 22, 'bold')).pack(side='left')
        tk.Label(title_row, text='Ali Games Edition', bg=HEADER, fg=GOLD2,
                 font=('Segoe UI', 22, 'bold')).pack(side='left')
        tk.Label(title, text='Auto Detect   •   Auto Connect   •   Error Analyzer   •   Web Solution',
                 bg=HEADER, fg=MUTED, font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(5, 0))

        right = tk.Frame(h, bg=HEADER)
        right.grid(row=0, column=2, sticky='e', padx=(6, 24), pady=(24, 17))
        status_row = tk.Frame(right, bg=HEADER)
        status_row.pack(anchor='e')
        tk.Label(status_row, text='USB-TTL', bg=HEADER, fg=TEXT,
                 font=('Segoe UI', 11, 'bold')).pack(side='left', padx=(0, 12))
        self.status = tk.Label(status_row, text='●  WAITING', bg=HEADER, fg=YELLOW,
                                font=('Segoe UI', 11, 'bold'))
        self.status.pack(side='left')
        self.status_detail = tk.Label(right, text='COM —   |   115200 bps', bg=HEADER,
                                      fg=MUTED, font=('Segoe UI', 10))
        self.status_detail.pack(anchor='e', pady=(8, 0))

    def card(self, parent, row, col, rowspan=1, colspan=1):
        f = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        f.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
               sticky='nsew', padx=6, pady=5)
        return f

    def heading(self, parent, text, color=GOLD2, height=42):
        bar = tk.Frame(parent, bg=PANEL, height=height)
        bar.pack(fill='x')
        bar.pack_propagate(False)
        tk.Label(bar, text=text, bg=PANEL, fg=color,
                 font=('Segoe UI', 13, 'bold')).pack(side='left', padx=15, pady=8)
        return bar

    def build_connection(self):
        c = tk.Frame(self.root, bg=PANEL, height=78,
                     highlightthickness=1, highlightbackground=BORDER)
        c.pack(fill='x', padx=14, pady=(10, 9))
        c.pack_propagate(False)

        # Deliberately fixed proportions so Clear Log / Save Log stay visible.
        c.grid_columnconfigure(0, weight=0, minsize=220)
        c.grid_columnconfigure(1, weight=0, minsize=150)
        c.grid_columnconfigure(2, weight=0, minsize=230)
        c.grid_columnconfigure(3, weight=1, minsize=260)

        left = tk.Frame(c, bg=PANEL)
        left.grid(row=0, column=0, sticky='nsew', padx=(17, 7), pady=11)
        tk.Label(left, text='COM PORT (AUTO DETECT)', bg=PANEL, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w')
        row = tk.Frame(left, bg=PANEL)
        row.pack(fill='x', pady=(5, 0))
        self.port = ttk.Combobox(row, width=8, state='readonly')
        self.port.pack(side='left', fill='x', expand=True, ipady=2)
        ttk.Button(row, text='↻', width=3, style='Dark.TButton',
                   command=lambda: self.refresh_ports(auto=True)).pack(side='left', padx=4)

        mid = tk.Frame(c, bg=PANEL)
        mid.grid(row=0, column=1, sticky='nsew', padx=7, pady=11)
        tk.Label(mid, text='BAUD RATE', bg=PANEL, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w')
        self.baud = ttk.Combobox(mid, values=['9600', '19200', '38400', '57600', '115200', '230400', '460800', '921600'], state='readonly')
        self.baud.set('115200')
        self.baud.pack(fill='x', pady=(5, 0), ipady=2)
        self.baud.bind('<<ComboboxSelected>>', self.on_baud_change)

        self.conn_box = tk.Frame(c, bg='#071a14', highlightthickness=1,
                                 highlightbackground='#0d7553', height=62)
        self.conn_box.grid(row=0, column=2, sticky='ew', padx=8, pady=15)
        self.conn_box.grid_propagate(False)
        self.conn_dot = tk.Label(self.conn_box, text='●', bg='#071a14', fg=GREEN,
                                 font=('Segoe UI', 18))
        self.conn_dot.pack(side='left', padx=(14, 5))
        tx = tk.Frame(self.conn_box, bg='#071a14')
        tx.pack(side='left', pady=8)
        self.conn_title = tk.Label(tx, text='USB-TTL Terdeteksi', bg='#071a14', fg=GREEN,
                                   font=('Segoe UI', 10, 'bold'))
        self.conn_title.pack(anchor='w')
        self.conn_detail = tk.Label(tx, text='COM —', bg='#071a14', fg=TEXT,
                                    font=('Segoe UI', 9))
        self.conn_detail.pack(anchor='w', pady=(1, 0))

        btns = tk.Frame(c, bg=PANEL)
        btns.grid(row=0, column=3, sticky='e', padx=(7, 16), pady=14)
        self.clear_btn = tk.Button(btns, text='Clear Log', command=self.clear_log,
                                   bg=PANEL2, fg=TEXT, activebackground='#17283b', activeforeground='#ffffff',
                                   font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
                                   highlightthickness=1, highlightbackground=BORDER,
                                   width=10, padx=10, pady=7)
        self.clear_btn.pack(side='left', padx=4)
        self.save_btn = tk.Button(btns, text='Save Log', command=self.save_log,
                                  bg=GOLD, fg='#11151a', activebackground=GOLD2, activeforeground='#11151a',
                                  font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
                                  highlightthickness=1, highlightbackground=GOLD2,
                                  width=10, padx=10, pady=7)
        self.save_btn.pack(side='left', padx=4)

    def build_uart_log(self, parent, r, c):
        f = self.card(parent, r, c)
        top = tk.Frame(f, bg=PANEL, height=43)
        top.pack(fill='x', padx=12)
        top.pack_propagate(False)
        tk.Label(top, text='▣  UART LOG', bg=PANEL, fg=CYAN,
                 font=('Segoe UI', 13, 'bold')).pack(side='left', padx=(2, 0), pady=8)
        right = tk.Frame(top, bg=PANEL)
        right.pack(side='right', pady=7)
        tk.Label(right, text='Auto Scroll', bg=PANEL, fg=TEXT,
                 font=('Segoe UI', 9)).pack(side='left', padx=(0, 7))
        self.autoscroll = tk.BooleanVar(value=True)
        tk.Checkbutton(right, variable=self.autoscroll, bg=PANEL, fg=CYAN,
                       selectcolor=PANEL2, activebackground=PANEL,
                       activeforeground=CYAN, bd=0, highlightthickness=0).pack(side='left')

        wrap = tk.Frame(f, bg=PANEL3, highlightthickness=1, highlightbackground=BORDER2)
        wrap.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.log = tk.Text(wrap, bg=PANEL3, fg='#dceaf6', insertbackground=CYAN,
                           selectbackground='#17344a', relief='flat',
                           font=('Consolas', 10), wrap='none', padx=12, pady=8,
                           spacing1=2, height=1, width=1)
        self.log.tag_configure('error', foreground=RED)
        self.log.tag_configure('warn', foreground=YELLOW)
        self.log.tag_configure('info', foreground=CYAN)
        self.log.tag_configure('normal', foreground=TEXT)
        sy = ttk.Scrollbar(wrap, orient='vertical', command=self.log.yview)
        sx = ttk.Scrollbar(wrap, orient='horizontal', command=self.log.xview)
        self.log.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.log.pack(side='left', fill='both', expand=True)
        sy.pack(side='right', fill='y')
        sx.pack(side='bottom', fill='x')

    def build_web(self, parent, r, c, rowspan=1):
        f = self.card(parent, r, c, rowspan=rowspan)
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        header = tk.Frame(f, bg=PANEL, height=43)
        header.grid(row=0, column=0, sticky='ew', padx=12)
        header.grid_propagate(False)
        tk.Label(header, text='◉  WEB SOLUTIONS', bg=PANEL, fg=CYAN,
                 font=('Segoe UI', 13, 'bold')).pack(side='left', pady=8)
        self.web_status = tk.Label(header, text='4 hasil ditemukan', bg=PANEL,
                                   fg=GREEN, font=('Segoe UI', 9, 'bold'))
        self.web_status.pack(side='right', pady=8)

        canvas_wrap = tk.Frame(f, bg=PANEL)
        canvas_wrap.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 8))
        canvas_wrap.grid_rowconfigure(0, weight=1)
        canvas_wrap.grid_columnconfigure(0, weight=1)
        self.web_canvas = tk.Canvas(canvas_wrap, bg=PANEL, highlightthickness=0, width=1, height=1)
        sb = ttk.Scrollbar(canvas_wrap, orient='vertical', command=self.web_canvas.yview)
        self.web_canvas.configure(yscrollcommand=sb.set)
        self.web_inner = tk.Frame(self.web_canvas, bg=PANEL)
        self.web_window_id = self.web_canvas.create_window((0, 0), window=self.web_inner, anchor='nw')
        self.web_inner.bind('<Configure>', lambda e: self.web_canvas.configure(scrollregion=self.web_canvas.bbox('all')))
        self.web_canvas.bind('<Configure>', lambda e: self.web_canvas.itemconfigure(self.web_window_id, width=max(1, e.width)))
        self.web_canvas.grid(row=0, column=0, sticky='nsew')
        sb.grid(row=0, column=1, sticky='ns')

        bottom = tk.Frame(f, bg=PANEL)
        bottom.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 10))
        bottom.grid_columnconfigure(0, weight=1)
        ttk.Button(bottom, text='COPY WEB SOLUTION', style='Gold.TButton',
                   command=self.copy_web_solution).grid(row=0, column=0, sticky='ew', ipady=3)
        self.render_web_placeholder()

    def render_web_placeholder(self):
        for w in self.web_inner.winfo_children():
            w.destroy()
        tk.Label(self.web_inner, text='Hasil pencarian error akan muncul otomatis di sini.',
                 bg=PANEL, fg=MUTED, font=('Segoe UI', 9), wraplength=300,
                 justify='center').pack(fill='x', padx=12, pady=30)

    def build_analyzer(self, parent, r, c):
        f = self.card(parent, r, c)
        top = tk.Frame(f, bg=PANEL, height=34)
        top.pack(fill='x', padx=12)
        top.pack_propagate(False)
        tk.Label(top, text='⌕  ERROR ANALYZER', bg=PANEL, fg=GOLD2,
                 font=('Segoe UI', 11, 'bold')).pack(side='left', pady=5)
        inner = tk.Frame(f, bg=PANEL)
        inner.pack(fill='both', expand=True, padx=12, pady=(0, 5))

        self.err_box = tk.Frame(inner, bg='#18080c', highlightthickness=1,
                                highlightbackground=RED, width=260, height=102)
        self.err_box.pack(side='left', fill='both', expand=True, padx=(0, 7))
        self.err_box.pack_propagate(False)
        tk.Label(self.err_box, text='⚠  Error Detected', bg='#18080c', fg=RED,
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(5, 1))
        self.err_text = tk.Label(self.err_box, text='Belum ada error terdeteksi.',
                                 bg='#18080c', fg=TEXT, font=('Segoe UI', 8, 'bold'),
                                 justify='left', wraplength=275)
        self.err_text.pack(anchor='w', padx=12, pady=(0, 6))

        self.diag = tk.Frame(inner, bg=PANEL2, highlightthickness=1,
                             highlightbackground='#6f5819', width=320, height=102)
        self.diag.pack(side='left', fill='both', expand=True, padx=(7, 0))
        self.diag.pack_propagate(False)
        tk.Label(self.diag, text='💡  Diagnosis & Solusi', bg=PANEL2, fg=GOLD2,
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(5, 1))
        self.diag_text = tk.Label(self.diag, text='Pencarian solusi web berjalan otomatis saat error UART terdeteksi.',
                                  bg=PANEL2, fg=TEXT, font=('Segoe UI', 8, 'bold'),
                                  justify='left', wraplength=335)
        self.diag_text.pack(anchor='w', padx=12, pady=(0, 6))

    def build_footer(self, parent, r, c, colspan=1):
        f = tk.Frame(parent, bg=PANEL, highlightthickness=1,
                     highlightbackground=BORDER, height=36)
        f.grid(row=r, column=c, columnspan=colspan, sticky='ew', padx=6, pady=4)
        f.grid_propagate(False)
        self.footer_msg = tk.Label(f, text='USB-TTL belum terhubung. Colokkan perangkat untuk auto-connect.',
                                   bg=PANEL, fg=MUTED, font=('Segoe UI', 7, 'bold'), anchor='w')
        self.footer_msg.pack(side='left', fill='x', expand=True, padx=14)
        tk.Label(f, text='Web search: automatic', bg=PANEL, fg=GOLD2,
                 font=('Segoe UI', 7, 'bold'), anchor='e').pack(side='right', padx=14)

    # ---------------------- USB / UART logic ----------------------
    def _port_is_usb_serial(self, p):
        text = ' '.join(str(x or '') for x in (p.description, p.manufacturer, getattr(p, 'product', ''), p.hwid)).lower()
        keys = ('usb', 'ttl', 'serial', 'ch340', 'ch341', 'cp210', 'ftdi', 'silicon labs', 'prolific')
        return any(k in text for k in keys)

    def refresh_ports(self, auto=False):
        ports = [] if list_ports is None else list(list_ports.comports())
        vals = [p.device for p in ports]
        self.port['values'] = vals
        if self.current_port and self.current_port in vals:
            self.port.set(self.current_port)
        elif vals and not self.port.get():
            self.port.set(vals[0])
        if auto and ports and not self.running:
            candidates = [p for p in ports if self._port_is_usb_serial(p)] or ports
            self.port.set(candidates[0].device)
            self.connect(candidates[0].device)
        elif not ports and not self.running:
            self.set_disconnected_state()

    def auto_monitor_ports(self):
        try:
            ports = [] if list_ports is None else list(list_ports.comports())
            names = {p.device for p in ports}
            added = names - self.last_port_names
            self.last_port_names = names
            self.port['values'] = [p.device for p in ports]

            if self.running and self.current_port and self.current_port not in names:
                old = self.current_port
                self.append_log(f'WARNING USB-TTL disconnected: {old}')
                self.disconnect(log=False)

            if not self.running and ports and added:
                candidates = [p for p in ports if p.device in added and self._port_is_usb_serial(p)]
                if not candidates:
                    candidates = [p for p in ports if p.device in added]
                chosen = candidates[0] if candidates else None
                if chosen:
                    self.port.set(chosen.device)
                    self.connect(chosen.device)
        except Exception:
            pass
        self.root.after(500, self.auto_monitor_ports)

    def on_baud_change(self, _=None):
        if self.running and self.current_port:
            p = self.current_port
            self.disconnect(log=False)
            self.root.after(100, lambda: self.connect(p))

    def connect(self, p):
        if serial is None:
            self.set_status('●  SERIAL ERROR', RED, 'pyserial tidak tersedia')
            self.set_connected_box(False, 'pyserial belum terpasang')
            return
        if self.running and self.current_port == p:
            return
        if self.running:
            self.disconnect(log=False)
        token = self.connection_token + 1
        self.connection_token = token
        try:
            baud = int(self.baud.get() or 115200)
            ser = serial.Serial(p, baud, timeout=0.25)
            self.ser = ser
            self.running = True
            self.current_port = p
            self.port.set(p)
            # Green state is only set after Serial() opens successfully.
            self.set_status('●  CONNECTED', GREEN, f'{p}   |   {baud} bps')
            self.set_connected_box(True, f'{p} - Connected')
            self.footer_msg.config(text=f'USB-TTL terdeteksi di {p}. Auto-connect berhasil.')
            self.append_log(f'INFO USB-TTL terdeteksi di {p}')
            self.append_log(f'INFO Baud rate: {baud}')
            self.append_log('INFO Koneksi UART berhasil')
            self.append_log('INFO Menunggu data...')
            threading.Thread(target=self.reader, args=(ser, token), daemon=True).start()
        except Exception as e:
            self.running = False
            self.ser = None
            self.current_port = None
            self.set_status('●  OPEN FAILED', RED, f'{p}')
            self.set_connected_box(False, f'{p} - gagal dibuka')
            self.footer_msg.config(text=f'USB-TTL terdeteksi di {p}, tetapi COM gagal dibuka.')
            self.append_log('ERROR COM open failed: ' + str(e))

    def set_connected_box(self, connected, detail):
        if connected:
            bg, border, fg, title = '#071a14', '#0d7553', GREEN, 'USB-TTL Terdeteksi'
        else:
            bg, border, fg, title = '#0e1723', BORDER, YELLOW, 'USB-TTL Menunggu'
        self.conn_box.config(bg=bg, highlightbackground=border)
        self.conn_dot.config(bg=bg, fg=fg)
        self.conn_title.config(bg=bg, fg=fg, text=title)
        self.conn_detail.config(bg=bg, fg=TEXT, text=detail)

    def set_disconnected_state(self, detail='Menunggu perangkat USB-TTL...'):
        self.set_status('●  WAITING', YELLOW, 'COM —   |   115200 bps')
        self.set_connected_box(False, detail)
        if hasattr(self, 'footer_msg'):
            self.footer_msg.config(text='USB-TTL belum terhubung. Colokkan perangkat untuk auto-connect.')

    def disconnect(self, log=True):
        self.connection_token += 1
        self.running = False
        old = self.current_port
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass
        self.ser = None
        self.current_port = None
        self.set_disconnected_state()
        if log and old:
            self.append_log(f'WARNING USB-TTL disconnected: {old}')

    def set_status(self, text, color, detail):
        self.status.config(text=text, fg=color)
        self.status_detail.config(text=detail)

    def reader(self, ser, token):
        while self.running and self.ser is ser and self.connection_token == token:
            try:
                data = ser.readline()
                if data:
                    self.q.put(data.decode('utf-8', 'replace').rstrip('\r\n'))
            except Exception as e:
                if self.connection_token == token:
                    self.q.put('ERROR UART read: ' + str(e))
                break

    def drain_queue(self):
        while not self.q.empty():
            self.append_log(self.q.get())
        self.root.after(100, self.drain_queue)

    def append_log(self, text):
        stamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        low = str(text).lower()
        iserr = bool(re.search(r'\b(error|failed|failure|timeout|exception|denied|fatal)\b', low)) or low.startswith('error:') or low.startswith('error |')
        iswarn = bool(re.search(r'\bwarning\b', low))
        tag = 'error' if iserr else ('warn' if iswarn else ('info' if 'info' in low else 'normal'))
        self.log.insert('end', f'[{stamp}]  {text}\n', tag)
        if self.autoscroll.get():
            self.log.see('end')
        if iserr:
            self.root.after(50, lambda e=str(text): self.handle_error(e))

    def handle_error(self, error):
        error = error.strip()
        key = error.lower()
        now = time.time()
        self.err_text.config(text=error)
        self.diag_text.config(text=self.local_diagnosis(error))
        if key != self.last_error_key or now - self.last_error_time > 3:
            self.last_error_key = key
            self.last_error_time = now
            self.search_web(error)

    def local_diagnosis(self, q):
        low = q.lower()
        hints = []
        if 'timeout' in low:
            hints += ['Periksa TX / RX / GND dan kabel USB-TTL.', 'Pastikan baud rate sesuai perangkat.', 'Periksa power, reset, dan respons target.']
        if 'permission' in low or 'access is denied' in low:
            hints += ['COM sedang dipakai aplikasi lain.', 'Tutup serial monitor lain.']
        if '0xffffffff' in low or 'invalid' in low or 'header' in low:
            hints += ['Periksa wiring dan level tegangan.', 'Pastikan target berada pada kondisi yang benar.']
        if 'com' in low or 'serial' in low:
            hints += ['Periksa driver USB-TTL dan COM Port.']
        if not hints:
            hints = ['Tidak ada pola spesifik. Hasil web akan mencari dokumentasi terkait pesan error ini.']
        return '\n'.join('✓  ' + x for x in dict.fromkeys(hints))

    def search_web(self, error):
        q = error.replace('\n', ' ')[:500]
        if not q:
            return
        if not any(k in q.lower() for k in ('uart', 'serial', 'ps4', 'nor', 'usb')):
            q += ' UART USB TTL PS4'
        self.web_status.config(text='Mencari solusi...', fg=CYAN)
        threading.Thread(target=self.web_worker, args=(q,), daemon=True).start()

    def web_worker(self, q):
        rows = []
        try:
            if requests is None:
                raise RuntimeError('requests belum terpasang')
            url = 'https://html.duckduckgo.com/html/?' + urllib.parse.urlencode({'q': q})
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            r.raise_for_status()
            blocks = re.findall(r'<a[^>]+class=["\']result__a["\'][^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r.text, re.S | re.I)
            for href, title in blocks[:8]:
                title = html.unescape(re.sub('<.*?>', '', title)).strip()
                href = html.unescape(href)
                m = re.search(r'uddg=([^&]+)', href)
                href = urllib.parse.unquote(m.group(1)) if m else href
                source = urllib.parse.urlparse(href).netloc or 'Web'
                rows.append((title, source, href))
        except Exception as e:
            rows = [('Pencarian web gagal', str(e), '')]
        self.root.after(0, lambda: self.show_results(rows))

    def show_results(self, rows):
        self.search_rows = rows
        for w in self.web_inner.winfo_children():
            w.destroy()
        for i, (title, source, href) in enumerate(rows):
            card = tk.Frame(self.web_inner, bg=PANEL2, highlightthickness=1,
                            highlightbackground=(CYAN if i == 0 else BORDER))
            card.pack(fill='x', padx=5, pady=5)
            tk.Label(card, text=title, bg=PANEL2, fg=TEXT,
                     font=('Segoe UI', 10, 'bold'), wraplength=330,
                     justify='left').pack(anchor='w', padx=12, pady=(10, 2))
            tk.Label(card, text=source, bg=PANEL2, fg=GOLD2,
                     font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=12)
            link = tk.Label(card, text=href, bg=PANEL2, fg=CYAN,
                            font=('Segoe UI', 8), cursor='hand2',
                            wraplength=330, justify='left')
            link.pack(anchor='w', padx=12, pady=(2, 8))
            if href:
                link.bind('<Button-1>', lambda e, u=href: webbrowser.open(u))
            card.bind('<Button-1>', lambda e, idx=i: self.select_web(idx))
            for child in card.winfo_children():
                child.bind('<Button-1>', lambda e, idx=i: self.select_web(idx))
        good = rows and rows[0][0] != 'Pencarian web gagal'
        self.web_status.config(text=f'{len(rows)} hasil ditemukan' if good else 'Web search gagal',
                               fg=GREEN if good else RED)

    def select_web(self, i):
        if 0 <= i < len(self.search_rows):
            self.selected_web = i

    def copy_web_solution(self):
        if not self.search_rows:
            return
        i = max(0, min(getattr(self, 'selected_web', 0), len(self.search_rows) - 1))
        title, source, href = self.search_rows[i]
        text = f'{title}\nSource: {source}\nLink: {href}'
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        self.footer_msg.config(text='Web solution berhasil disalin ke clipboard.')

    def clear_log(self):
        self.log.delete('1.0', 'end')
        self.footer_msg.config(text='UART Log sudah dibersihkan.')

    def save_log(self):
        p = filedialog.asksaveasfilename(defaultextension='.txt',
                                         filetypes=[('Text', '*.txt'), ('All files', '*.*')])
        if p:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(self.log.get('1.0', 'end'))
            self.footer_msg.config(text=f'Log tersimpan: {os.path.basename(p)}')

    def on_close(self):
        self.disconnect(log=False)
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
