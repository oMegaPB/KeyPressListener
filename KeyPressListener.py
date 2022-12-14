import win32api, win32gui, win32process
import re, asyncio
from types import TracebackType
from typing import Callable, Union, Coroutine, Any, Optional, Type
# ------------------------------------------------------------------------------------------------------
class KeyEventArgs: # i saw this name somewhere :thonk:
    __slots__ = ('keycode', 'key', 'shift', 'caps')
    def __init__(self, key: str, keycode: int, shift: bool, caps: bool) -> None:
        self.keycode = keycode
        self.key = key
        self.shift = shift
        self.caps = caps
    def __repr__(self) -> str:
        sequence = self.key if self.key != "\n" else "\\n"
        return f'<KeyEventArgs: "Key": "{sequence}", "keycode": {self.keycode}, "shift": {self.shift}, "caps": {self.caps}>'
# ------------------------------------------------------------------------------------------------------
xFunction = Union[Callable[[KeyEventArgs], Any], Coroutine[Any, Any, Any]]
# ------------------------------------------------------------------------------------------------------
class KeyPressEventListener:
    def __init__(self, on_press: xFunction = None, on_release: xFunction = None) -> None:
        self.previous = {}
        self.on_press = on_press
        self.on_release = on_release
        self.none = {
            1: 'MouseLeft', 2: 'MouseRight', 8: 'BackSpace', 9: 'Tab', 13: 'Enter', 16: 'Shift', 
            19: 'Pause', 20: 'CapsLock', 27: 'Esc', 32: 'Space', 33: 'PgUp', 34: 'PgDown', 35: 'End', 
            36: 'Home', 37: 'Left', 38: 'Up', 39: 'Right', 40: 'Down', 44: 'PrSc', 45: 'Insert', 
            46: 'Delete', 92: 'Win', 93: 'Select', 112: 'F1', 113: 'F2', 114: 'F3', 115: 'F4', 
            116: 'F5', 117: 'F6', 118: 'F7', 119: 'F8', 120: 'F9', 121: 'F10', 122: 'F11', 123: 'F12', 
            144: 'NumLock', 145: 'ScLock', 164: 'Alt'
        }
    def __enter__(self) -> "KeyPressEventListener":
        return self
    
    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        return False
    
    def GetKeyboardLayoutID(self) -> int:
        return int(hex(win32api.GetKeyboardLayout(win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]) & (2**16 - 1)), 16)
    
    def ToUnicodeEx(self, keycode: int) -> str:
        if keycode == 17: return 'Ctrl'
        if keycode in [222, 192] and not win32api.GetAsyncKeyState(17) in [-32768, -32767]: # Ctrl
            shift = win32api.GetAsyncKeyState(0x10) in [-32768, -32767]
            lid = self.GetKeyboardLayoutID()
            shift = not shift if (win32api.GetKeyState(0x14) == 1) else shift
            if keycode == 192: # dead Key
                if lid == 1049: # ru layout
                    if not shift: return '??'
                    else: return '??'
                elif lid == 1033: # en layout
                    if not shift: return '`'
                    else: return '~'
            elif keycode == 222: # another dead Key
                if lid == 1049:
                    if not shift: return '??'
                    else: return '??'
                elif lid == 1033:
                    if not shift: return "'"
                    else: return '"'
        key: bytes = win32api.ToAsciiEx(keycode, 0, win32api.GetKeyboardState(), win32api.GetKeyboardLayout())
        if key and re.fullmatch(r'[A-z??-??0-9\?\.!";=\-/,*\+@#$%\^^&(){}<>~???????:]', key.decode('cp1251')):
            return key.decode('cp1251')
        return self.none.get(keycode, None) if not win32api.GetAsyncKeyState(17) in [-32768, -32767] else None
    
    def _dispatch(self, keycode: int, event: xFunction) -> bool:
        if event:
            caps = win32api.GetKeyState(0x14) == 1
            shift = win32api.GetAsyncKeyState(0x10) in [-32768, -32767]
            sequence = self.ToUnicodeEx(keycode)
            if sequence:
                if asyncio.iscoroutinefunction(event):
                    return asyncio.run_coroutine_threadsafe(event(KeyEventArgs(sequence, keycode, shift, caps))) in [None, True]
                return event(KeyEventArgs(sequence, keycode, shift, caps)) in [None, True]
        return True

    def join(self) -> None: # return False in "on_press/on_release" to stop
        while True:
            win32api.Sleep(15)
            for i in range(255):
                state = win32api.GetKeyState(i)
                if state == -127 or state == -128:
                    if self.previous.get(i) is None:
                        self.previous[i] = state
                        if not self._dispatch(keycode=i, event=self.on_press):
                            return
                else:
                    if self.previous.get(i) is not None:
                        self.previous.pop(i)
                        if not self._dispatch(keycode=i, event=self.on_release):
                            return
                
# ------------------------------------------------------------------------------------------------------
# async def myFunction(e: KeyEventArgs): # example on_press/on_release function (can be async)
#     if e.key == 'q':
#         return False
#     elif e.key == 'h':
#         print('hello from the keyboard!')
#     else:
#         print(e)
# with KeyPressEventListener(on_release=myFunction) as listener:
#     listener.join()
# ------------------------------------------------------------------------------------------------------
with KeyPressEventListener(on_release=lambda e: print(e)) as listener:
    listener.join()
