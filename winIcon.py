from win32com.shell import shell, shellcon
from PIL import Image, ImageTk
import win32api
import win32con
import win32ui
import win32gui
import os

LARGE = "large"
SMALL = "small"

def get_icon(PATH, size):
    #print("\nPath: ", PATH, "Type: ", type(PATH), "Count: ", count, "\n")

    SHGFI_ICON = 0x000000100
    SHGFI_ICONLOCATION = 0x000001000
    if size == "small":
        SHIL_SIZE = 0x00001
    elif size == "large":
        SHIL_SIZE = 0x00002
    else:
        raise TypeError("Invalid argument for 'size'. Must be equal to 'small' or 'large'")
        
    try:    
        ret, info = shell.SHGetFileInfo(PATH, 0, SHGFI_ICONLOCATION | SHGFI_ICON | SHIL_SIZE)
        hIcon, iIcon, dwAttr, name, typeName = info
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_x)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), hIcon)
        win32gui.DestroyIcon(hIcon)

        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            "RGBA",
            (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr, "raw", "BGRA", 0, 1
        )
    except win32ui.error:
        raise WinIconError("Couldn't get icon for '%s'" % PATH)
        return

    if size == "small":
        img = img.resize((16, 16), Image.ANTIALIAS)
    return img

class WinIconError(Exception):
    pass