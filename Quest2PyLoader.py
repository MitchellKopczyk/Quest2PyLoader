import tkinter as tk
from tkinter import filedialog
import os
import subprocess
import threading

def check_device():
    while True:
        result = os.popen('adb devices -l').read()
        if 'device' in result and 'model:Quest' in result:
            label.config(text='Quest Device is Connected', fg='green')
            update_list()
            break

def update_list():
    result = os.popen('adb shell ls /storage/emulated/0/Android/data').read()
    listbox.delete(0, tk.END)
    for item in result.split('\n'):
        listbox.insert(tk.END, item)

def push():
    folder = filedialog.askdirectory()
    if folder:
        label.config(text='Pushing folder...')
        result = os.system(f'adb push "{folder}" /storage/emulated/0/Android/data')
        if result == 0:
            label.config(text='Folder pushed!')
        else:
            label.config(text='An error occurred while pushing the folder.')
        update_list()

def install():
    file = filedialog.askopenfilename(filetypes=[('APK files', '*.apk')])
    if file:
        label.config(text='Installing APK...')
        result = subprocess.check_output(f'adb install -r "{file}"', shell=True).decode()
        label.config(text=result)

root = tk.Tk()
root.title('Quest2PyLoader')

os.system('adb kill-server')
os.system('adb start-server')

label = tk.Label(root, text='Connect the Quest Headset and Allow USB Debugging inside the headset', fg='red')
label.pack()

listbox = tk.Listbox(root)
listbox.pack(fill=tk.BOTH, expand=True, padx=10)

push_button = tk.Button(root, text='Push Folder', command=push)
push_button.pack()

install_button = tk.Button(root, text='Install APK', command=install)
install_button.pack()

threading.Thread(target=check_device).start()

root.mainloop()