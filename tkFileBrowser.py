from glob import glob
from operator import itemgetter
import tkinter as tk
from tkinter import ttk
from win32com.shell import shell, shellcon
from tkinter import messagebox
from PIL import Image, ImageTk
import win32api
import win32con
import win32ui
import win32gui
import os

#stuff to do:
#   fix the icon error, even though I literally have changed nothing to do with them
#   and they've stopped working for some reason

#   make the files actually refresh instead of just detecting it

#   keep  current nodes open when a new drive is plugged in

class TkFileBrowser(tk.Frame):

    _open = []

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

    def see(self, path):
        """Open the tree and book to this folder
        
        Arguments:
            path {str} -- path to open to
        """
        if not os.path.exists(path):
            raise FileNotFoundError("The system couldn't find the path: '%s'" % path)
            return

        #open the correct book tab
        split = path.replace("\\", "/").split("/")

        #if requested is file, go to the folder in which it's in
        if os.path.isfile(path):
            del split[-1]
        
        drive = split[0] + "\\"
        self._book.select(self._book._get_drives().index(drive))

        try:
            self._book._tabs[drive]._tree.see("\\".join(split))
        except tk.TclError:
            #the node probably isn't loaded yet so we have to make it load before
            #using .see()
            for i in range(len(split) - 1):
                self._book._tabs[drive]._populate_path("\\".join(split[:i+2]))
                self._book._tabs[drive]._tree.item("\\".join(split[:i+2]), open = True)
                
                #add to list of open nodes
                self._open.append([split[0]+"\\", "\\".join(split[:i+2])])

            self._book._tabs[drive]._tree.see("\\".join(split))

    def refresh(self):
        self._book._refresh()

        #TODO: update root nodes too

        #print(self._open)

        #work out which open nodes need to be updated
        nodes_to_refresh = []
        for i in self._open:
            dir = i[1]
            if not os.path.exists(dir):
                continue
            #work out all the dirs that the node is showing, ignoring the dummy by checking for paths
            childirs = [p.split("\\")[-1] for p in self._book._tabs[i[0]]._tree.get_children(dir) if os.path.exists(p)]
            
            #work out all the dirs that are in the file system. Use our own method so that settings
            #are still here, show hidden files, etc.
            files, folders = self._book._tabs[i[0]]._get_dirs_in_path(dir)
            actualdirs = files + folders

            print(dir, actualdirs == childirs)

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

    _foldericons = {}
    _fileicons = {}
    _tabs = {}

    def __init__(self, parent):
        ttk.Notebook.__init__(self)
        self._parent = parent

        self._draw_tabs()

    def _draw_tabs(self):
        self._drive_icons = self._get_icons()   #store to attribute so it doesn't get removed by garbage deletion
        for drive in self._drive_icons:
            self._tabs[drive[0]] = FileTree(self, drive[0])
            if os.path.split(drive[0])[1] != "":
                self.add(self._tabs[drive[0]], text = "Home", image = drive[1], compound = tk.LEFT)
            else:
                self.add(self._tabs[drive[0]], text = drive[0], image = drive[1], compound = tk.LEFT)

    def _refresh(self):
        """Checks if a drive as been added or removed. If it has, tabs are refreshed.
        """

        #check if we need to refresh before refreshing
        if list(map(itemgetter(0), self._drive_icons)) != self._get_drives():
            display = [i[0] for i in self._drive_icons]
            new = self._get_drives()

            removals = list(set(display).difference(new))
            additions = list(set(new).difference(display))

            #print("removed: ", removals, "added: ", additions)
            
            for removal in removals:
                #delete open nodes that have just been removed
                self._parent._open = [i for i in self._parent._open if i[0] != removal]

                #deelte the tab
                try:
                    self.forget(self._tabs[removal])
                except tk.TclError:
                    #TODO: work out why this throws an error when it still works
                    pass

                #remove from tab dictionary
                del self._tabs[removal]

                #reset drive icons
                self._drive_icons = [i for i in self._drive_icons if i[0] != removal]

            if additions != []:
                for tab in self.tabs():
                    self.forget(tab)
                
                self._draw_tabs()

    def _get_drives(self):
        return [os.path.expanduser("~")] + win32api.GetLogicalDriveStrings().split('\x00')[:-1]

    def _get_icons(self):
        drives = self._get_drives()
        return [[drive, ImageTk.PhotoImage(self._parent._get_icon(drive, "small"))] for drive in drives]

    def _get_tab_name(self):
        """Returns the name of the tab which is currently open
        
        Returns:
            int -- the name of the tab that's currently open e.g. C:\\, C:\\Users\\Fred
        """

        return self._get_drives()[self.index(self.select())]

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
        self._tree.bind('<<TreeviewClose>>', self._on_close)

    def _on_click(self, event):
        id = os.path.normpath(self._tree.focus())

        #add to the list of open nodes
        if os.path.isdir(id):
            #add both the tab name and the path, since the same path could be open in multiple places
            self._parent._parent._open.append([self._parent._get_tab_name(), id])
            #print(self._parent._parent._open)

        if os.path.isfile(id):
            self._command(id)
        else:
            try:
                self._populate_path(id)
            except tk.TclError:
                #this node has already been opened, so delete children and load again
                for child in self._tree.get_children(id):
                    self._tree.delete(child)
                self._populate_path(id)

        print("\n clicked: ", self._parent._parent._open)

    def _on_close(self, event):
        """Method called when the user closes a node. This must delete the node,
        and it's children, from the list of open nodes. To do this, a recursive
        algoritm is used. We have to use this, as opposed to something like os.walk()
        for preformance. A large folder could have thousands of children. This doesn't
        'go deeper' unless the node in the tree is open.
        
        Arguments:
            event {tkinter event} -- tkinter event is used to get the id,
        """

        id = os.path.normpath(self._tree.focus())
        drive = self._parent._get_tab_name()

        def recurse(path):
            glob_pattern = os.path.join(path, '*')
            for dir in sorted(glob(glob_pattern), key=os.path.getctime):
                if os.path.isdir(dir) and self._tree.item(dir, "open"):
                    self._parent._parent._open.remove([drive, dir])
                    recurse(dir)

        try:
            self._parent._parent._open.remove([drive, id])
        except ValueError:
            #already removed by parent
            pass

        recurse(id)
    
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
        #if the tree is blank, write to the root
        if self._tree.get_children() == ():
            node = ""
        else:
            node = path

        folders, files = self._get_dirs_in_path(path)

        for folder in folders:
            fullpath = os.path.join(path, folder)
            self._tree.insert(
                parent = node, 
                index = tk.END, 
                iid = fullpath,
                tag = fullpath,
                text = folder,
                image = self._parent._foldericons[fullpath],
                values = [folder, "", ""])
            #setup a dummy so the '+' appears before it's loaded. Child stuff will be loaded when the user
            #clicks on the plus, and the dummy will be removed. (or not if there are no files)
            self._tree.insert(parent = fullpath, index = tk.END, tag = "dummy", text = "No avaliable files")

        for file in files:
            fullpath = os.path.join(path, file)
            name, type_ = os.path.splitext(file)
            #if the type is a shortcut, get the whole path as a key
            if type_ == ".lnk" or type_ == ".exe":
                icon = self._parent._fileicons[fullpath]
            else:
                icon = self._parent._fileicons[type_]
            self._tree.insert(
                parent = node, 
                index = tk.END, 
                iid = fullpath,
                tag = fullpath,
                text = file,
                image = icon,
                values = [file, "", self._get_size(fullpath)])

        #if there is more than one child, delete every child that isn't a path
        #and hence delete the dummy
        children = self._tree.get_children(node)
        if len(children) > 1:
            for child in children:
                if not os.path.exists(child):
                    self._tree.delete(child)

    def _get_dirs_in_path(self, path):
        """Returns two lists, the first is a list of all folders in a directory,
        the second is a list of files. Also loads the icons for these files and folders.
        For folders, it puts a tk.PhotoImage as the value of the _foldericons dictionary
        with the key being the full folder path. For files, it uses the _fileicons dictionary,
        with they key being the filetype, e.g. "mp4". If the file is a shortcut (".lnk") or
        executable (".exe"),  set the whole path as the key, since the icon is different for 
        every file of that type.
        
        Arguments:
            path {str} -- full path to the folder
        
        Returns:
            tuple -- two lists of folders and files.
        """

        def add(p, type_):
            files.append(p)

            #if the file is a shortcut, set the key as the whole path
            if type_ == ".lnk" or type_ == ".exe":
                self._parent._fileicons[os.path.join(path, p)] = ImageTk.PhotoImage(
                    self._parent._parent._get_icon(os.path.join(path, p), "small"))
            else:
                if type_ not in self._parent._fileicons:
                    self._parent._fileicons[type_] = ImageTk.PhotoImage(
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
                if os.path.join(path, p) not in self._parent._foldericons:
                    self._parent._foldericons[os.path.join(path, p)] = ImageTk.PhotoImage(
                        self._parent._parent._get_icon(os.path.join(path, p), "small"))

        #print("\n\nfolders: ", folders, "\nfiles: ", files)
        return folders, files

def on_click(path):
    print("click: ", path)

if __name__ == "__main__":
    root = tk.Tk()
    browser = TkFileBrowser(root, command = on_click)
    browser.pack(side = tk.LEFT)

    ttk.Button(root, text = "Goto", command = lambda: browser.see(r"C:\Users\Edward\Documents\random_pyapps\tkFileBrowser\tkFileBrowser\empty_folder")).pack(side = tk.LEFT)

    root.mainloop()