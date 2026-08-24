import os
import sys
import tkinter as tk
import webbrowser
from pathlib import Path

import customtkinter as ctk


SUPPORT_URL = "https://buycoffee.to/beniamin-tv6"


def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).resolve().parent.parent / "assets" / filename


def apply_window_icon(window):
    png_path = resource_path("app_icon.png")
    ico_path = resource_path("app_icon.ico")

    if png_path.exists():
        try:
            window._app_icon_photo = tk.PhotoImage(file=str(png_path))
            window.iconphoto(True, window._app_icon_photo)
        except tk.TclError:
            pass

    if ico_path.exists():
        try:
            window.iconbitmap(str(ico_path))
        except tk.TclError:
            pass


def open_support_page():
    webbrowser.open(SUPPORT_URL)


def _find_parent(parent=None):
    if parent is not None:
        return parent
    return tk._default_root


def show_styled_dialog(title, message, kind="info", parent=None):
    parent = _find_parent(parent)
    if parent is None:
        return None

    accents = {
        "info": "#2f8cff",
        "warning": "#f59e0b",
        "error": "#ef4444",
    }
    accent = accents.get(kind, accents["info"])

    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("540x300")
    dialog.minsize(460, 250)
    dialog.resizable(False, False)
    dialog.transient(parent)
    apply_window_icon(dialog)

    card = ctk.CTkFrame(
        dialog,
        corner_radius=18,
        fg_color=("#f7f9fc", "#0d1726"),
        border_width=1,
        border_color=("#d8e1ec", "#1f3147"),
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(
        card,
        text=title,
        font=ctk.CTkFont("Segoe UI", 19, "bold"),
        text_color=accent,
        anchor="w",
    ).grid(row=0, column=0, padx=22, pady=(20, 10), sticky="ew")

    ctk.CTkLabel(
        card,
        text=str(message),
        font=ctk.CTkFont("Segoe UI", 13),
        text_color=("#26364a", "#d8e7fb"),
        justify="left",
        anchor="nw",
        wraplength=470,
    ).grid(row=1, column=0, padx=22, pady=(0, 14), sticky="nsew")

    def close_dialog():
        try:
            dialog.grab_release()
        except tk.TclError:
            pass
        dialog.destroy()

    ctk.CTkButton(
        card,
        text="OK",
        width=110,
        height=36,
        corner_radius=10,
        fg_color=accent,
        hover_color=accent,
        command=close_dialog,
    ).grid(row=2, column=0, padx=22, pady=(0, 20), sticky="e")

    dialog.protocol("WM_DELETE_WINDOW", close_dialog)
    dialog.update_idletasks()
    parent.update_idletasks()
    x = parent.winfo_rootx() + max((parent.winfo_width() - dialog.winfo_width()) // 2, 0)
    y = parent.winfo_rooty() + max((parent.winfo_height() - dialog.winfo_height()) // 2, 0)
    dialog.geometry(f"+{x}+{y}")
    dialog.grab_set()
    dialog.focus_force()
    parent.wait_window(dialog)
    return "ok"


class StyledMessageBox:
    @staticmethod
    def showinfo(title, message, **kwargs):
        return show_styled_dialog(title, message, "info", kwargs.get("parent"))

    @staticmethod
    def showwarning(title, message, **kwargs):
        return show_styled_dialog(title, message, "warning", kwargs.get("parent"))

    @staticmethod
    def showerror(title, message, **kwargs):
        return show_styled_dialog(title, message, "error", kwargs.get("parent"))


styled_messagebox = StyledMessageBox()
