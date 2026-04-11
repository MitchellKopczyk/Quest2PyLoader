import os
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, Listbox, StringVar
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#00D4FF"
ACCENT_DIM = "#0099BB"
BG_DEEP = "#0A0C10"
BG_MID = "#111420"
BG_CARD = "#161B27"
BG_HOVER = "#1E2535"
BORDER = "#1E2A3E"
TEXT_PRIMARY = "#E8EDF5"
TEXT_MUTED = "#5A6A85"
TEXT_DANGER = "#FF4C6A"
TEXT_SUCCESS = "#00C896"
TEXT_WARN = "#FFB340"

connected = False
selected_item = None

def check_device():
    global connected
    while True:
        try:
            result = os.popen('adb devices -l').read()
            if 'device' in result and 'model:Quest' in result:
                if not connected:
                    connected = True
                    app.after(0, lambda: on_device_connected())
            else:
                if connected:
                    connected = False
                    app.after(0, lambda: on_device_disconnected())
        except Exception:
            pass
        time.sleep(2)

def on_device_connected():
    status_dot.configure(fg_color=TEXT_SUCCESS)
    status_text.configure(text="Quest Connected", text_color=TEXT_SUCCESS)
    device_pill.configure(fg_color="#0D2A22", text_color=TEXT_SUCCESS, text="● ONLINE")
    update_list()

def on_device_disconnected():
    status_dot.configure(fg_color=TEXT_DANGER)
    status_text.configure(text="No Device Found", text_color=TEXT_MUTED)
    device_pill.configure(fg_color="#2A0D14", text_color=TEXT_DANGER, text="○ OFFLINE")
    listbox.delete(0, "end")
    show_status("Device disconnected.", "warn")

def show_status(msg, kind="info"):
    colors = {
        "info": ACCENT,
        "success": TEXT_SUCCESS,
        "error": TEXT_DANGER,
        "warn": TEXT_WARN,
        "loading": TEXT_WARN,
    }
    icons = {
        "info": "→",
        "success": "✓",
        "error": "✕",
        "warn": "!",
        "loading": "↻",
    }
    status_bar.configure(
        text=f"  {icons.get(kind, '·')}  {msg}",
        text_color=colors.get(kind, TEXT_MUTED)
    )

def update_list():
    try:
        result = os.popen('adb shell ls /storage/emulated/0/Android/data').read()
        listbox.delete(0, "end")
        items = [i.strip() for i in result.split('\n') if i.strip()]
        for item in items:
            listbox.insert("end", item)
        count_label.configure(text=f"{len(items)} packages")
    except Exception as e:
        show_status(f"Failed to list packages: {e}", "error")

def push():
    if not connected:
        show_status("No device connected.", "error")
        return
    folder = filedialog.askdirectory(title="Select folder to push")
    if folder:
        show_status("Pushing folder...", "loading")
        def do_push():
            result = os.system(f'adb push "{folder}" /storage/emulated/0/Android/data')
            if result == 0:
                app.after(0, lambda: show_status("Folder pushed successfully.", "success"))
            else:
                app.after(0, lambda: show_status("Push failed. Check ADB connection.", "error"))
            app.after(0, update_list)
        threading.Thread(target=do_push, daemon=True).start()

def install():
    if not connected:
        show_status("No device connected.", "error")
        return
    file = filedialog.askopenfilename(
        title="Select APK to install",
        filetypes=[("APK files", "*.apk")]
    )
    if file:
        show_status("Installing APK...", "loading")
        def do_install():
            try:
                result = subprocess.check_output(f'adb install -r "{file}"', shell=True).decode()
                if "Success" in result:
                    app.after(0, lambda: show_status("APK installed successfully.", "success"))
                else:
                    app.after(0, lambda: show_status(f"Install failed: {result.strip()}", "error"))
            except Exception as e:
                app.after(0, lambda: show_status(f"Error: {e}", "error"))
            app.after(0, update_list)
        threading.Thread(target=do_install, daemon=True).start()

def delete():
    if not connected:
        show_status("No device connected.", "error")
        return
    selected = listbox.curselection()
    if not selected:
        show_status("Select a package first.", "warn")
        return
    folder_name = listbox.get(selected[0])
    escaped = folder_name.replace(" ", "\\ ")
    show_status(f"Deleting {folder_name}...", "loading")
    def do_delete():
        result = os.system(f'adb shell rm -r "/storage/emulated/0/Android/data/{escaped}"')
        if result == 0:
            app.after(0, lambda: show_status(f"Deleted {folder_name}.", "success"))
        else:
            app.after(0, lambda: show_status("Delete failed.", "error"))
        app.after(0, update_list)
    threading.Thread(target=do_delete, daemon=True).start()

def extract():
    if not connected:
        show_status("No device connected.", "error")
        return
    selected = listbox.curselection()
    if not selected:
        show_status("Select a package first.", "warn")
        return
    folder_name = listbox.get(selected[0])
    escaped = folder_name.replace(" ", "\\ ")
    local_dir = filedialog.askdirectory(title="Choose extraction destination")
    if local_dir:
        show_status(f"Extracting {folder_name}...", "loading")
        def do_extract():
            result = os.system(f'adb pull "/storage/emulated/0/Android/data/{escaped}" "{local_dir}"')
            if result == 0:
                app.after(0, lambda: show_status("Extraction complete.", "success"))
            else:
                app.after(0, lambda: show_status("Extraction failed.", "error"))
            app.after(0, update_list)
        threading.Thread(target=do_extract, daemon=True).start()
    else:
        show_status("No destination selected.", "warn")

def on_listbox_select(evt):
    sel = listbox.curselection()
    if sel:
        name = listbox.get(sel[0])
        selected_label.configure(text=name, text_color=ACCENT)

def filter_list(*args):
    query = search_var.get().lower()
    try:
        result = os.popen('adb shell ls /storage/emulated/0/Android/data').read()
        items = [i.strip() for i in result.split('\n') if i.strip()]
        listbox.delete(0, "end")
        filtered = [i for i in items if query in i.lower()] if query else items
        for item in filtered:
            listbox.insert("end", item)
        count_label.configure(text=f"{len(filtered)} packages")
    except Exception:
        pass

app = ctk.CTk()
app.title("Quest2PyLoader")
app.geometry("680x600")
app.resizable(False, False)
app.configure(fg_color=BG_DEEP)

header = ctk.CTkFrame(app, fg_color=BG_MID, corner_radius=0, height=64)
header.pack(fill="x", side="top")
header.pack_propagate(False)

header_inner = ctk.CTkFrame(header, fg_color="transparent")
header_inner.pack(fill="both", expand=True, padx=20)

logo_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
logo_frame.pack(side="left", fill="y")

logo_mark = ctk.CTkLabel(
    logo_frame,
    text="Q2",
    font=("Courier", 18, "bold"),
    text_color=ACCENT,
    width=40, height=40,
    fg_color="#0D1E2A",
    corner_radius=8,
)
logo_mark.pack(side="left", padx=(0, 10), pady=12)

title_stack = ctk.CTkFrame(logo_frame, fg_color="transparent")
title_stack.pack(side="left", fill="y", pady=14)

ctk.CTkLabel(
    title_stack,
    text="Quest2PyLoader",
    font=("Courier", 15, "bold"),
    text_color=TEXT_PRIMARY,
    anchor="w"
).pack(anchor="w")

ctk.CTkLabel(
    title_stack,
    text="Meta Quest Sideload Tool",
    font=("Courier", 10),
    text_color=TEXT_MUTED,
    anchor="w"
).pack(anchor="w")

device_pill = ctk.CTkLabel(
    header_inner,
    text="○ OFFLINE",
    font=("Courier", 11, "bold"),
    fg_color="#2A0D14",
    text_color=TEXT_DANGER,
    corner_radius=20,
    padx=14, pady=5,
)
device_pill.pack(side="right", pady=18)

div = ctk.CTkFrame(app, fg_color=BORDER, height=1, corner_radius=0)
div.pack(fill="x")

body = ctk.CTkFrame(app, fg_color="transparent")
body.pack(fill="both", expand=True, padx=18, pady=14)

left_panel = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=12, width=420)
left_panel.pack(side="left", fill="both", expand=True)
left_panel.pack_propagate(False)

search_row = ctk.CTkFrame(left_panel, fg_color="transparent")
search_row.pack(fill="x", padx=14, pady=(14, 6))

search_var = StringVar()
search_var.trace_add("write", filter_list)

search_entry = ctk.CTkEntry(
    search_row,
    textvariable=search_var,
    placeholder_text="Filter packages...",
    font=("Courier", 12),
    fg_color="#0D1020",
    border_color=BORDER,
    text_color=TEXT_PRIMARY,
    placeholder_text_color=TEXT_MUTED,
    corner_radius=6,
    height=32,
)
search_entry.pack(side="left", fill="x", expand=True)

count_label = ctk.CTkLabel(
    search_row,
    text="0 packages",
    font=("Courier", 10),
    text_color=TEXT_MUTED,
)
count_label.pack(side="right", padx=(10, 0))

lb_frame = ctk.CTkFrame(left_panel, fg_color="#0D1020", corner_radius=8)
lb_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

listbox = Listbox(
    lb_frame,
    font=("Courier", 11),
    bg="#0D1020",
    fg="#8BA3C8",
    selectbackground="#0D2A3E",
    selectforeground=ACCENT,
    bd=0,
    highlightthickness=0,
    activestyle="none",
    relief="flat",
)
listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)
listbox.bind("<<ListboxSelect>>", on_listbox_select)

scrollbar = ctk.CTkScrollbar(lb_frame, command=listbox.yview, width=8)
scrollbar.pack(side="right", fill="y", pady=4)
listbox.config(yscrollcommand=scrollbar.set)

selected_label = ctk.CTkLabel(
    left_panel,
    text="No package selected",
    font=("Courier", 10),
    text_color=TEXT_MUTED,
    anchor="w",
)
selected_label.pack(anchor="w", padx=16, pady=(0, 10))

right_panel = ctk.CTkFrame(body, fg_color="transparent", width=200)
right_panel.pack(side="right", fill="y", padx=(14, 0))
right_panel.pack_propagate(False)

conn_card = ctk.CTkFrame(right_panel, fg_color=BG_CARD, corner_radius=10)
conn_card.pack(fill="x", pady=(0, 14))

conn_inner = ctk.CTkFrame(conn_card, fg_color="transparent")
conn_inner.pack(padx=14, pady=12)

dot_row = ctk.CTkFrame(conn_inner, fg_color="transparent")
dot_row.pack(fill="x")

status_dot = ctk.CTkLabel(
    dot_row,
    text="",
    width=10, height=10,
    fg_color=TEXT_DANGER,
    corner_radius=5,
)
status_dot.pack(side="left")

status_text = ctk.CTkLabel(
    dot_row,
    text="No Device Found",
    font=("Courier", 11),
    text_color=TEXT_MUTED,
)
status_text.pack(side="left", padx=(8, 0))

ctk.CTkLabel(
    conn_inner,
    text="Enable USB Debugging\nin Developer Settings",
    font=("Courier", 9),
    text_color=TEXT_MUTED,
    justify="left",
    anchor="w",
).pack(anchor="w", pady=(6, 0))

ctk.CTkLabel(
    right_panel,
    text="ACTIONS",
    font=("Courier", 10, "bold"),
    text_color=TEXT_MUTED,
    anchor="w",
).pack(anchor="w", pady=(0, 8))

def make_action_btn(parent, label, cmd, color=ACCENT, icon="→"):
    btn = ctk.CTkButton(
        parent,
        text=f"{icon}  {label}",
        command=cmd,
        font=("Courier", 12, "bold"),
        fg_color="transparent",
        hover_color=BG_HOVER,
        border_color=BORDER,
        border_width=1,
        text_color=color,
        corner_radius=8,
        height=38,
        anchor="w",
    )
    btn.pack(fill="x", pady=3)
    return btn

make_action_btn(right_panel, "Push Folder",    push,    TEXT_PRIMARY, "↑")
make_action_btn(right_panel, "Install APK",    install, TEXT_SUCCESS,  "⬡")
make_action_btn(right_panel, "Extract Folder", extract, TEXT_WARN,    "↓")
make_action_btn(right_panel, "Delete Folder",  delete,  TEXT_DANGER,  "✕")

ctk.CTkFrame(right_panel, fg_color=BORDER, height=1).pack(fill="x", pady=10)

refresh_btn = ctk.CTkButton(
    right_panel,
    text="↻  Refresh",
    command=update_list,
    font=("Courier", 11),
    fg_color="transparent",
    hover_color=BG_HOVER,
    border_color=BORDER,
    border_width=1,
    text_color=TEXT_MUTED,
    corner_radius=8,
    height=32,
)
refresh_btn.pack(fill="x")

bottom_bar = ctk.CTkFrame(app, fg_color=BG_MID, corner_radius=0, height=32)
bottom_bar.pack(fill="x", side="bottom")
bottom_bar.pack_propagate(False)

status_bar = ctk.CTkLabel(
    bottom_bar,
    text="  ·  Connect your Quest headset and allow USB Debugging.",
    font=("Courier", 11),
    text_color=TEXT_MUTED,
    anchor="w",
)
status_bar.pack(side="left", fill="y")

ctk.CTkLabel(
    bottom_bar,
    text="v2.0  ",
    font=("Courier", 10),
    text_color=TEXT_MUTED,
    anchor="e",
).pack(side="right")

thread = threading.Thread(target=check_device, daemon=True)
thread.start()

app.mainloop()
