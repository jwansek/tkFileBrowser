l = [['C:\\Users\\Edward', 'C:\\Users\\Edward\\Documents'], ['C:\\Users\\Edward', 'C:\\Users\\Edward\\Documents\\random_pyapps'], ['C:\\Users\\Edward', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser'], ['C:\\Users\\Edward', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser\\tkFileBrowser']]

out = []
search = 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser'


def get_drive_and_path(search):
    out = []
    for i in l:
        if i[1] == search:
            out.append(i)
    return out

print(get_drive_and_path(search))

[['C:\\', 'C:\\Users'], ['C:\\', 'C:\\Users\\Edward'], ['C:\\', 'C:\\Users\\Edward\\Documents'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser\\tkFileBrowser'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser\\tkFileBrowser\\empty_folder'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser\\tkFileBrowser\\temp']]
[['C:\\', 'C:\\Users'], ['C:\\', 'C:\\Users\\Edward'], ['C:\\', 'C:\\Users\\Edward\\Documents'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser\\tkFileBrowser\\empty_folder'], ['C:\\', 'C:\\Users\\Edward\\Documents\\random_pyapps\\tkFileBrowser\\tkFileBrowser\\temp']]