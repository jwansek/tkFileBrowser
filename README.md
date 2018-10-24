# tkFileBrowser
A file browser designed for use with Python tkinter applications

![Demo image](https://github.com/jwansek/tkFileBrowser/blob/master/demoimage.png?raw=true)

* Uses the Windows API to get the exact icon for any folder or application.
* Refreshes when drives are added or removed
* Final version will refresh the tree too

## Example Usage

    def on_click(path):
        print("click: ", path)

    if __name__ == "__main__":
        root = tk.Tk()
        browser = TkFileBrowser(root, on_click)
        browser.pack(side = tk.LEFT)

        ttk.Button(root, text = "Goto", command = lambda: browser.see(r"C:\Any\file\or\folder")).pack(side = tk.LEFT)

        root.mainloop()

## Documentation
TkFileBrowser(parent, command, [refresh = 20], [types = []], [showhidden = False])

> parent

Frame in which the widget will be placed

>command

Function to be run when the user clicks on a file. The path is an argument

>refresh

How often to check for updates in the file system. Default 20ms

>types

List of file types that will show up. Empty means all files. Default []

>showhidden

Show hidden files "." or not. Default False

>.see(path)

Open all nodes to a path and ensure it is shown on screen

More coming!
