# Lightweight functional check for the USB indicator logic without real hardware.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent/'src'))
import uart_ali_games as uag
import tkinter as tk

class P:
    def __init__(self, device, description='USB-SERIAL CH340'):
        self.device=device; self.description=description; self.manufacturer='USB'; self.product='CH340'; self.hwid='USB VID:PID=1A86:7523'

class Ports:
    state=[]
    @classmethod
    def comports(cls): return list(cls.state)

class FakeSerial:
    def __init__(self, p, baud, timeout=0.25): self.port=p; self.baudrate=baud; self.closed=False
    def readline(self): return b''
    def close(self): self.closed=True

orig_ports, orig_serial = uag.list_ports, uag.serial
Ports.state=[P('COM5')]
uag.list_ports=Ports
uag.serial=type('S',(),{'Serial':FakeSerial})

root=tk.Tk(); root.withdraw()
app=uag.App(root)
root.update()
assert app.running and app.current_port=='COM5', 'auto-connect failed'
Ports.state=[]
app.auto_monitor_ports(); root.update()
assert not app.running and app.current_port is None, 'disconnect detection failed'
app.on_close()
uag.list_ports, uag.serial = orig_ports, orig_serial
print('USB indicator functional check: PASS (auto-connect + disconnect)')
