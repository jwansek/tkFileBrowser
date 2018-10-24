from operator import itemgetter
import tkinter as tk
from tkinter import ttk
from win32com.shell import shell, shellcon
from PIL import Image, ImageTk
import win32api
import win32con
import win32ui
import win32gui
import os

class TkFileBrowser(tk.Frame):

    open = ""

    def __init__(self, parent, command, refresh = 20, types = [], showhidden = False):
        """Widget for browsing a windows filesystem.
        
        Arguments:
            parent {tk.Frame} -- parent frame
            command {function} -- Called when the user clicks on a file
        
        Keyword Arguments:
            refresh {int} -- how often to refresh browser (ms) (default: {20})
            types {list} -- file types that show up. Leave blank for all files: e
                e.g. [".png", ".jpg"] (default: {[]})
            showhiddem {bool} -- should the tree show hidden files or not (default: {False})
        """

        tk.Frame.__init__(self, parent)
        self._parent = parent
        self._command = command
        self._refresh = refresh
        self._types = types
        self._showhidden = showhidden

        self._book = DriveBook(self)
        self._book.pack(fill = tk.BOTH, expand = True)
        self.after(self._refresh, self.refresh)

    def open_to(self, path):
        """Open the tree and book to this folder
        
        Arguments:
            path {str} -- path to open to
        """
        #TODO: make this function
        raise NotImplementedError


    def refresh(self):
        self._book._refresh()
        self.after(self._refresh, self.refresh)

    def _get_icon(self, PATH, size):
        """Gets the icon association for any folder or file in the system
        
        Arguments:
            PATH {str} -- path to file or folder
            size {str} -- equal to "small" or "large". Indicates to return the 16x16 image or 32x32 image
        
        Raises:
            TypeError -- Thrown if invalid arguments are given
        
        Returns:
            PIL.Image -- PIL Image of the icon at the correct size
        """

        #https://stackoverflow.com/questions/21070423/python-sAaving-accessing-file-extension-icons-and-using-them-in-a-tkinter-progra/52957794#52957794
        #https://aecomputervision.blogspot.com/2018/10/getting-icon-association-for-any-file.html
        SHGFI_ICON = 0x000000100
        SHGFI_ICONLOCATION = 0x000001000
        if size == "small":
            SHIL_SIZE = 0x00001
        elif size == "large":
            SHIL_SIZE = 0x00002
        else:
            raise TypeError("Invalid argument for 'size'. Must be equal to 'small' or 'large'")
            
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

        if size == "small":
            img = img.resize((16, 16), Image.ANTIALIAS)
        return img

class DriveBook(ttk.Notebook):

    foldericons = {}
    fileicons = {}

    def __init__(self, parent):
        ttk.Notebook.__init__(self)
        self._parent = parent

        self._draw_tabs()

    def _draw_tabs(self):
        self._drive_icons = self._get_icons()   #store to attribute so it doesn't get removed by garbage deletion
        for drive in self._drive_icons:
            if os.path.split(drive[0])[1] != "":
                self.add(FileTree(self, drive[0]), text = "Home", image = drive[1], compound = tk.LEFT)
            else:
                self.add(FileTree(self, drive[0]), text = drive[0], image = drive[1], compound = tk.LEFT)

    def _refresh(self):
        """Checks if a drive as been added or removed. If it has, tabs are refreshed.
        """

        #check if we need to refresh before refreshing
        if list(map(itemgetter(0), self._drive_icons)) != self._get_drives():
            #TODO: make a more efficient way of updading drive list than deleting all of them and re-making
            for tab in self.tabs():
                self.forget(tab)
            
            self._draw_tabs()

    def _get_drives(self):
        return [os.path.expanduser("~")] + win32api.GetLogicalDriveStrings().split('\x00')[:-1]

    def _get_icons(self):
        drives = self._get_drives()
        return [[drive, ImageTk.PhotoImage(self._parent._get_icon(drive, "small"))] for drive in drives]


class FileTree(tk.Frame):
    def __init__(self, parent, drive):
        tk.Frame.__init__(self, parent)
        self._parent = parent
        self._command = self._parent._parent._command
        self._types = self._parent._parent._types
        self._showhidden = self._parent._parent._showhidden

        self._tree = ttk.Treeview(self, height = 20, columns = ('path', 'filetype', 'size'), displaycolumns = 'size')
        self._tree.heading('#0', text = 'Directory', anchor = tk.W)
        self._tree.heading('size', text = 'Size', anchor = tk.W)
        self._tree.column('path', width = 180)
        self._tree.column('size', stretch = 1, width = 48)
        self._tree.grid(row = 0, column = 0, sticky = 'nsew')

        sbr_y = ttk.Scrollbar(self, orient = tk.VERTICAL, command = self._tree.yview)
        sbr_x = ttk.Scrollbar(self, orient = tk.HORIZONTAL, command = self._tree.xview)
        self._tree['yscroll'] = sbr_y.set
        self._tree['xscroll'] = sbr_x.set
        sbr_y.grid(row = 0, column = 1, sticky = 'ns')
        sbr_x.grid(row = 1, column = 0, sticky = 'ew')
        
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

        self._populate_path(drive)
        self._tree.bind('<<TreeviewOpen>>', self._on_click)

    def _on_click(self, event):
        id = os.path.normpath(self._tree.focus())
        if os.path.isfile(id):
            self._command(id)
        else:
            self._populate_path(id)
    
    def _get_size(self, path):
        """Returns the size of a file. From:
        https://pyinmyeye.blogspot.co.uk/2012/07/tkinter-multi-column-list-demo.html
        
        Arguments:
            path {str} -- Path to file
        
        Returns:
            str -- file size in bytes/KB/MB/GB
        """

        size = os.path.getsize(path)
        KB = 1024.0
        MB = KB * KB
        GB = MB * KB
        if size >= GB:
            return ('{:,.1f} GB').format(size / GB)
        elif size >= MB:
            return ('{:,.1f} MB').format(size / MB)
        elif size >= KB:
            return ('{:,.1f} KB').format(size / KB)
        else:
            return ('{} bytes').format(size)

    def _populate_path(self, path):
        print("path:", path)
        if path in self._parent._get_drives():
            node = ""
        else:
            node = path

        folders, files = self._get_dirs_in_path(path)
        print("node:", node)

        for folder in folders:
            fullpath = os.path.join(path, folder)
            print("fullpath:", fullpath)
            self._tree.insert(
                parent = node, 
                index = tk.END, 
                iid = fullpath,
                tag = fullpath,
                text = folder,
                image = self._parent.foldericons[fullpath],
                values = [folder, "", ""])
            self._tree.insert(parent = fullpath, index = tk.END, tag = "dummy", text = "No avaliable files")

        for file in files:
            fullpath = os.path.join(path, file)
            name, type_ = os.path.splitext(file)
            self._tree.insert(
                parent = node, 
                index = tk.END, 
                iid = fullpath,
                tag = fullpath,
                text = file,
                image = self._parent.fileicons[type_],
                values = [file, "", self._get_size(fullpath)])

    def _get_dirs_in_path(self, path):
        """Returns two lists, the first is a list of all folders in a directory,
        the second is a list of files. Also loads the icons for these files and folders.
        For folders, it puts a tk.PhotoImage as the value of the foldericons dictionary
        with the key being the full folder path. For files, it uses the fileicons dictionary,
        with they key being the filetype, e.g. "mp4".
        
        Arguments:
            path {str} -- full path to the folder
        
        Returns:
            tuple -- two lists of folders and files.
        """

        def add(p, type_):
            files.append(p)
            if type_ not in self._parent.fileicons:
                self._parent.fileicons[type_] = ImageTk.PhotoImage(
                    self._parent._parent._get_icon(os.path.join(path, p), "small"))

        files = []
        folders = []
        for p in os.listdir(path):
            if p.startswith(".") and not self._showhidden:
                continue
            
            if os.path.isfile(os.path.join(path, p)):
                name, type_ = os.path.splitext(p)
                if self._types == []:
                    add(p, type_)
                else:
                    if type_ in self._types:
                        add(p, type_)
                
            else:
                folders.append(p)
                if os.path.join(path, p) not in self._parent.foldericons:
                    self._parent.foldericons[os.path.join(path, p)] = ImageTk.PhotoImage(
                        self._parent._parent._get_icon(os.path.join(path, p), "small"))

        #print("\n\nfolders: ", folders, "\nfiles: ", files)
        return folders, files


def on_click(path):
    print("click: ", path)

if __name__ == "__main__":
    root = tk.Tk()
    browser = TkFileBrowser(root, on_click)
    browser.pack()

    root.mainloop()