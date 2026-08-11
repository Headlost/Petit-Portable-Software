import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import os
import sys
import webbrowser
from pillow_heif import register_heif_opener
from PIL import Image
from app_common import apply_window_icon, styled_messagebox as messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

APP_VERSION = "2.0.0"
APP_AUTHOR = "Beniamin Żak"
SUPPORT_URLS = {
    "pl": "https://buycoffee.to/beniamin-tv6",
    "en": "https://ko-fi.com/beniaminzak",
}

COLORS = {
    "background": "#2f2114",
    "surface": "#24180f",
    "surface_raised": "#382719",
    "control": "#21160e",
    "control_hover": "#44301b",
    "border": "#75611f",
    "border_bright": "#f0c94d",
    "primary": "#171914",
    "primary_hover": "#2b2513",
    "selected": "#b88916",
    "selected_hover": "#d3a725",
    "accent": "#f2c94c",
    "accent_soft": "#ffe895",
    "heic_blue": "#38bdf8",
    "text": "#f7f4e8",
    "muted": "#aaa58f",
}

TRANSLATIONS = {
    "pl": {
        "window_title": "Konwerter HEIC -> JPG",
        "app_title": "Konwerter HEIC do JPG",
        "main_title": "Konwerter HEIC → JPG",
        "subtitle": "Szybka konwersja wielu zdjęć bez zmiany plików źródłowych",
        "description": "Konwertuje pojedyncze lub liczne obrazy HEIC do formatu JPG.",
        "language": "Wybierz język",
        "convert": "Wybierz pliki i konwertuj",
        "choose_output": "Wybierz folder zapisu",
        "open_output": "Otwórz folder zapisu",
        "support": "Wsparcie",
        "about": "O mnie",
        "about_title": "O programie",
        "name": "Nazwa",
        "version": "Wersja",
        "author": "Autor",
        "tooltip": (
            "Jeśli nie wybierzesz folderu zapisu, pliki JPG zostaną zapisane "
            "w folderach, w których znajdują się pliki HEIC."
        ),
        "choose_output_dialog": "Wybierz folder zapisu plików JPG",
        "output_title": "Folder zapisu",
        "choose_output_first": "Najpierw wybierz folder zapisu lub wykonaj konwersję.",
        "output_missing": "Wybrany folder zapisu już nie istnieje.",
        "output_open_failed": "Nie udało się otworzyć folderu:\n{error}",
        "choose_files_dialog": "Wybierz pliki HEIC do konwersji",
        "heic_files": "Pliki HEIC",
        "all_files": "Wszystkie pliki",
        "conversion_failed": "Nie udało się skonwertować pliku {path}: {error}",
        "information": "Informacja",
        "conversion_success": "Skonwertowano pomyślnie {count} plików.",
    },
    "en": {
        "window_title": "HEIC to JPG Converter",
        "app_title": "HEIC to JPG Converter",
        "main_title": "HEIC → JPG Converter",
        "subtitle": "Fast conversion of multiple photos without modifying source files",
        "description": "Converts one or multiple HEIC images to JPG format.",
        "language": "Choose language",
        "convert": "Select files and convert",
        "choose_output": "Choose output folder",
        "open_output": "Open output folder",
        "support": "Support",
        "about": "About",
        "about_title": "About",
        "name": "Name",
        "version": "Version",
        "author": "Author",
        "tooltip": (
            "If you do not choose an output folder, JPG files will be saved "
            "in the folders containing the selected HEIC files."
        ),
        "choose_output_dialog": "Choose a folder for JPG files",
        "output_title": "Output folder",
        "choose_output_first": "Choose an output folder or convert files first.",
        "output_missing": "The selected output folder no longer exists.",
        "output_open_failed": "Could not open the output folder:\n{error}",
        "choose_files_dialog": "Select HEIC files to convert",
        "heic_files": "HEIC files",
        "all_files": "All files",
        "conversion_failed": "Could not convert {path}: {error}",
        "information": "Information",
        "conversion_success": "Successfully converted {count} file(s).",
    },
}

selected_output_directory = None
last_output_directory = None
current_language = "pl"


def tr(key):
    return TRANSLATIONS[current_language][key]


class HoverTooltip:
    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id = None
        self._window = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def set_text(self, text):
        self.text = text
        self._hide()

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        self._after_id = None
        if self._window is not None or not self.widget.winfo_exists():
            return

        widget_width = self.widget.winfo_width()
        tooltip_width = max(widget_width - 4, 260)
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self._window = tk.Toplevel(self.widget)
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.configure(bg=COLORS["surface_raised"])
        self._window.geometry(f"+{x}+{y}")

        tooltip_frame = ctk.CTkFrame(
            self._window,
            width=tooltip_width,
            corner_radius=9,
            fg_color=COLORS["surface_raised"],
            border_width=1,
            border_color=COLORS["border_bright"],
        )
        tooltip_frame.pack(padx=2, pady=2)

        ctk.CTkLabel(
            tooltip_frame,
            text=self.text,
            width=tooltip_width - 28,
            fg_color="transparent",
            text_color=COLORS["text"],
            justify="left",
            anchor="w",
            wraplength=max(tooltip_width - 28, 200),
        ).pack(padx=14, pady=8)

    def _hide(self, _event=None):
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None


def show_about():
    messagebox.showinfo(
        tr("about_title"),
        (
            f"{tr('name')}: {tr('app_title')}\n"
            f"{tr('version')}: {APP_VERSION}\n"
            f"{tr('author')}: {APP_AUTHOR}\n\n"
            f"{tr('description')}"
        ),
    )


def open_support_page():
    webbrowser.open(SUPPORT_URLS[current_language])


def choose_output_directory():
    global selected_output_directory

    directory = filedialog.askdirectory(
        title=tr("choose_output_dialog"),
        initialdir=selected_output_directory or os.path.expanduser("~"),
    )
    if directory:
        selected_output_directory = os.path.normpath(directory)


def open_output_directory():
    directory = selected_output_directory or last_output_directory
    if not directory:
        messagebox.showwarning(
            tr("output_title"),
            tr("choose_output_first"),
        )
        return

    if not os.path.isdir(directory):
        messagebox.showerror(
            tr("output_title"),
            tr("output_missing"),
        )
        return

    try:
        os.startfile(directory)
    except OSError as error:
        messagebox.showerror(
            tr("output_title"),
            tr("output_open_failed").format(error=error),
        )


def convert_files():
    global last_output_directory

    # Zarejestruj obsługę plików HEIF/HEIC
    register_heif_opener()

    file_paths = filedialog.askopenfilenames(
        title=tr("choose_files_dialog"),
        filetypes=[(tr("heic_files"), "*.heic"), (tr("all_files"), "*.*")]
    )

    if not file_paths:
        return  # Użytkownik nie wybrał plików

    sukcesy = 0
    for path in file_paths:
        try:
            img = Image.open(path)
            output_directory = selected_output_directory or os.path.dirname(path)
            base_name = os.path.splitext(os.path.basename(path))[0]
            new_path = os.path.join(output_directory, base_name + ".jpg")
            img.save(new_path, "JPEG", quality=90)
            last_output_directory = output_directory
            sukcesy += 1
        except Exception as error:
            print(tr("conversion_failed").format(path=path, error=error))

    messagebox.showinfo(
        tr("information"),
        tr("conversion_success").format(count=sukcesy),
    )

def main():
    global current_language

    root = ctk.CTk()
    root.title(tr("window_title"))
    root.geometry("560x500")
    root.resizable(False, False)
    root.configure(fg_color=COLORS["background"])
    apply_window_icon(root)

    main_title_label = ctk.CTkLabel(
        root,
        text=tr("main_title"),
        font=ctk.CTkFont("Segoe UI", 28, "bold"),
        text_color=COLORS["text"],
    )
    main_title_label.pack(anchor="w", padx=30, pady=(30, 8))
    subtitle_label = ctk.CTkLabel(
        root,
        text=tr("subtitle"),
        text_color=COLORS["muted"],
    )
    subtitle_label.pack(anchor="w", padx=30, pady=(0, 22))

    language_panel = ctk.CTkFrame(
        root,
        width=112,
        height=112,
        corner_radius=0,
        fg_color="transparent",
        border_width=0,
    )
    language_panel.place(relx=1.0, x=-24, y=24, anchor="ne")
    language_panel.pack_propagate(False)
    ctk.CTkLabel(
        language_panel,
        text=f"v{APP_VERSION}",
        height=25,
        corner_radius=12,
        fg_color=COLORS["control"],
        text_color=COLORS["accent"],
        border_width=1,
        border_color=COLORS["border_bright"],
        font=ctk.CTkFont("Segoe UI", 11, "bold"),
    ).pack(fill="x", padx=16, pady=(10, 5))
    language_label = ctk.CTkLabel(
        language_panel,
        text=tr("language"),
        height=18,
        font=ctk.CTkFont("Segoe UI", 10, "bold"),
        text_color=COLORS["text"],
    )
    language_label.pack()

    card = ctk.CTkFrame(
        root,
        corner_radius=18,
        fg_color=COLORS["surface"],
        border_width=1,
        border_color=COLORS["border"],
    )
    card.pack(fill="both", expand=True, padx=30, pady=(0, 22))
    ctk.CTkLabel(card, text="HEIC", font=ctk.CTkFont("Segoe UI", 34, "bold"),
                 text_color=COLORS["heic_blue"]).pack(pady=(28, 0))
    ctk.CTkLabel(card, text="↓", font=ctk.CTkFont("Segoe UI", 28),
                 text_color=COLORS["text"]).pack(pady=2)
    ctk.CTkLabel(card, text="JPG", font=ctk.CTkFont("Segoe UI", 34, "bold"),
                 text_color=COLORS["accent_soft"]).pack()
    convert_button = ctk.CTkButton(
        card,
        text=tr("convert"),
        height=44,
        font=ctk.CTkFont("Segoe UI", 14, "bold"),
        fg_color=COLORS["primary"],
        hover_color=COLORS["primary_hover"],
        border_width=1,
        border_color=COLORS["border_bright"],
        text_color=COLORS["accent"],
        command=convert_files,
    )
    convert_button.pack(fill="x", padx=24, pady=(20, 10))
    convert_button._output_tooltip = HoverTooltip(
        convert_button,
        tr("tooltip"),
    )

    folder_actions = ctk.CTkFrame(card, fg_color="transparent")
    folder_actions.pack(fill="x", padx=24, pady=(0, 22))
    choose_output_button = ctk.CTkButton(
        folder_actions,
        text=tr("choose_output"),
        height=38,
        fg_color="transparent",
        hover_color=COLORS["control_hover"],
        border_width=1,
        border_color=COLORS["border_bright"],
        text_color=COLORS["text"],
        command=choose_output_directory,
    )
    choose_output_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
    open_output_button = ctk.CTkButton(
        folder_actions,
        text=tr("open_output"),
        height=38,
        fg_color="transparent",
        hover_color=COLORS["control_hover"],
        border_width=1,
        border_color=COLORS["border_bright"],
        text_color=COLORS["text"],
        command=open_output_directory,
    )
    open_output_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

    footer = ctk.CTkFrame(root, fg_color="transparent")
    footer.pack(fill="x", padx=30, pady=(0, 12))
    support_button = ctk.CTkButton(
        footer,
        text=tr("support"),
        width=110,
        fg_color="transparent",
        hover_color=COLORS["control_hover"],
        border_width=1,
        border_color=COLORS["border_bright"],
        text_color=COLORS["text"],
        command=open_support_page,
    )
    support_button.pack(side="left")
    about_button = ctk.CTkButton(
        footer,
        text=tr("about"),
        width=110,
        fg_color="transparent",
        hover_color=COLORS["control_hover"],
        border_width=1,
        border_color=COLORS["border_bright"],
        text_color=COLORS["text"],
        command=show_about,
    )
    about_button.pack(side="right")

    ctk.CTkLabel(root, text="© 2024 Beniamin Żak", text_color=COLORS["muted"],
                 font=ctk.CTkFont("Segoe UI", 11, slant="italic")).pack(pady=(0, 16))

    def change_language(selected_language):
        global current_language

        current_language = selected_language.lower()
        root.title(tr("window_title"))
        main_title_label.configure(text=tr("main_title"))
        subtitle_label.configure(text=tr("subtitle"))
        language_label.configure(text=tr("language"))
        convert_button.configure(text=tr("convert"))
        convert_button._output_tooltip.set_text(tr("tooltip"))
        choose_output_button.configure(text=tr("choose_output"))
        open_output_button.configure(text=tr("open_output"))
        support_button.configure(text=tr("support"))
        about_button.configure(text=tr("about"))

    language_selector = ctk.CTkSegmentedButton(
        language_panel,
        values=["PL", "EN"],
        width=76,
        height=26,
        corner_radius=8,
        border_width=1,
        fg_color=COLORS["control"],
        selected_color=COLORS["selected"],
        selected_hover_color=COLORS["selected_hover"],
        unselected_color=COLORS["control"],
        unselected_hover_color=COLORS["control_hover"],
        text_color=COLORS["text"],
        font=ctk.CTkFont("Segoe UI", 10, "bold"),
        command=change_language,
    )
    language_selector.pack(pady=(3, 9))
    language_selector.set(current_language.upper())

    root.mainloop()

if __name__ == "__main__":
    main()
