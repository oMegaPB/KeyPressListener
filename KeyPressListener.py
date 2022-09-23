import win32api, win32gui, win32process
import re, asyncio
from typing_extensions import Self
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
class KeyPressEventListener:
    def __init__(self, on_press: Union[Callable[[KeyEventArgs], Any], Coroutine[Any, Any, Any]]) -> None:
        self.previous = {}
        self.need_to_await = False
        if asyncio.iscoroutinefunction(on_press):
            self.need_to_await = True
        self.on_press = on_press
        self.none = {
            1: 'MouseLeft', 2: 'MouseRight', 8: 'BackSpace', 9: 'Tab', 13: 'Enter', 16: 'Shift', 
            19: 'Pause', 20: 'CapsLock', 27: 'Esc', 32: 'Space', 33: 'PgUp', 34: 'PgDown', 35: 'End', 
            36: 'Home', 37: 'Left', 38: 'Up', 39: 'Right', 40: 'Down', 44: 'PrSc', 45: 'Insert', 
            46: 'Delete', 92: 'Win', 93: 'Select', 112: 'F1', 113: 'F2', 114: 'F3', 115: 'F4', 
            116: 'F5', 117: 'F6', 118: 'F7', 119: 'F8', 120: 'F9', 121: 'F10', 122: 'F11', 123: 'F12', 
            144: 'NumLock', 145: 'ScLock', 164: 'Alt'
        }
    def __enter__(self) -> Self:
        return self
    
    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> bool:
        return False
    
    def GetKeyboardLayoutID(self) -> int:
        return int(hex(win32api.GetKeyboardLayout(win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]) & (2**16 - 1)), 16)
    
    async def ToUnicodeEx(self, keycode: int) -> str:
        if keycode == 17: return 'Ctrl'
        if keycode in [222, 192] and not win32api.GetAsyncKeyState(17) in [-32768, -32767]: # Ctrl
            shift = win32api.GetAsyncKeyState(0x10) in [-32768, -32767]
            lid = self.GetKeyboardLayoutID()
            shift = not shift if (win32api.GetKeyState(0x14) == 1) else shift
            if keycode == 192:
                if lid == 1049: # ru layout
                    if not shift: return 'ё'
                    else: return 'Ё'
                elif lid == 1033: # en layout
                    if not shift: return '`'
                    else: return '~'
            elif keycode == 222:
                if lid == 1049:
                    if not shift: return 'э'
                    else: return 'Э'
                elif lid == 1033:
                    if not shift: return "'"
                    else: return '"'
        key: bytes = win32api.ToAsciiEx(keycode, 0, win32api.GetKeyboardState(), win32api.GetKeyboardLayout())
        if key and re.fullmatch(r'[A-zА-я0-9\?\.!";=\-/,*\+@#$%\^^&(){}<>~ёЁ№:]', key.decode('cp1251')):
            return key.decode('cp1251')
        return self.none.get(keycode, None) if not win32api.GetAsyncKeyState(17) in [-32768, -32767] else None
    
    async def _dispatch(self, keycode: int) -> Optional[bool]:
        caps = win32api.GetKeyState(0x14) == 1
        shift = win32api.GetAsyncKeyState(0x10) in [-32768, -32767]
        sequence = await self.ToUnicodeEx(keycode)
        if sequence:
            if self.need_to_await:
                return await self.on_press(KeyEventArgs(sequence, keycode, shift, caps)) in [None, True]
            return self.on_press(KeyEventArgs(sequence, keycode, shift, caps)) in [None, True]
        return True

    async def join(self) -> None: # return False in "on_press" to stop
        while True:
            win32api.Sleep(15)
            for i in range(255):
                state = win32api.GetKeyState(i)
                if state == -127 or state == -128:
                    if self.previous.get(i) is None:
                        self.previous[i] = state
                        if not await self._dispatch(i):
                            return
                    else:
                        if self.previous[i] != state:
                            self.previous[i] = state
                            if not await self._dispatch(i):
                                return
# ------------------------------------------------------------------------------------------------------
# async def on_press(e: KeyEventArgs): # example on_press function
#     if e.key == 'q':
#         return False
#     elif e.key == 'h':
#         print('hello from the keyboard!')
#     else:
#         print(e)
# ------------------------------------------------------------------------------------------------------
async def main():
    with KeyPressEventListener(on_press=lambda e: print(e)) as listener:
        await listener.join()
asyncio.new_event_loop().run_until_complete(main())
