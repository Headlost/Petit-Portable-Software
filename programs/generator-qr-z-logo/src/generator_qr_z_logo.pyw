import os
import traceback
import tkinter as tk
import webbrowser
from tkinter import filedialog

import customtkinter as ctk
import qrcode
from PIL import Image, ImageDraw, ImageFont

from app_common import apply_window_icon, styled_messagebox as messagebox


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_VERSION = "4.8.0"
APP_AUTHOR = "Beniamin Żak"
SUPPORT_URLS = {
    "pl": "https://buycoffee.to/beniamin-tv6",
    "en": "https://ko-fi.com/beniaminzak",
}

TRANSLATIONS = {
    "pl": {
        "window_title": "Generator kodów QR",
        "app_title": "Generator kodów QR",
        "app_name": "Generator kodów QR z logo",
        "subtitle": "Utwórz kod QR i umieść własne logo w jego centrum",
        "description": "Tworzy kody QR z opcjonalnym logo i estetycznym obramowaniem.",
        "qr_content": "Treść kodu QR",
        "placeholder": "Numer, tekst lub adres URL",
        "choose_logo": "Wybierz logo",
        "no_logo": "Nie wybrano pliku",
        "generate": "Generuj kod QR",
        "choose_output": "Wybierz folder zapisu",
        "open_output": "Otwórz folder zapisu",
        "pin": "Przypnij",
        "support": "Wsparcie  ♥",
        "about": "O mnie",
        "about_title": "O programie",
        "name": "Nazwa",
        "version": "Wersja",
        "author": "Autor",
        "choose_logo_dialog": "Wybierz plik logo",
        "image_files": "Pliki graficzne",
        "png_files": "Pliki PNG",
        "save_dialog": "Zapisz kod QR jako...",
        "choose_output_dialog": "Wybierz folder zapisu kodów QR",
        "input_error_title": "Błąd",
        "input_error": "Podaj treść do zakodowania.",
        "success_title": "Sukces",
        "success": "Kod QR zapisano jako:\n{path}",
        "unexpected_error_title": "Błąd nieoczekiwany",
        "unexpected_error": "Wystąpił błąd:\n{error}",
        "folder_title": "Folder zapisu",
        "generate_first": "Najpierw wygeneruj i zapisz kod QR.",
        "folder_missing": "Folder z wygenerowanym plikiem już nie istnieje.",
        "folder_open_failed": "Nie udało się otworzyć folderu:\n{error}",
    },
    "en": {
        "window_title": "QR Code Generator",
        "app_title": "QR Code Generator",
        "app_name": "QR Code Generator with Logo",
        "subtitle": "Create a QR code and place your own logo in its center",
        "description": "Creates QR codes with an optional logo and a stylish border.",
        "qr_content": "QR code content",
        "placeholder": "Number, text, or URL",
        "choose_logo": "Choose logo",
        "no_logo": "No file selected",
        "generate": "Generate QR code",
        "choose_output": "Choose output folder",
        "open_output": "Open output folder",
        "pin": "Pin",
        "support": "Support  ♥",
        "about": "About",
        "about_title": "About",
        "name": "Name",
        "version": "Version",
        "author": "Author",
        "choose_logo_dialog": "Choose a logo file",
        "image_files": "Image files",
        "png_files": "PNG files",
        "save_dialog": "Save QR code as...",
        "choose_output_dialog": "Choose a folder for QR codes",
        "input_error_title": "Error",
        "input_error": "Enter the content to encode.",
        "success_title": "Success",
        "success": "QR code saved as:\n{path}",
        "unexpected_error_title": "Unexpected error",
        "unexpected_error": "An error occurred:\n{error}",
        "folder_title": "Output folder",
        "generate_first": "Generate and save a QR code first.",
        "folder_missing": "The folder containing the generated file no longer exists.",
        "folder_open_failed": "Could not open the folder:\n{error}",
    },
}


class QRCodeApp:
    def __init__(self, root):
        self.root = root
        self.current_language = "pl"
        self.logo_path = None
        self.selected_output_directory = None
        self.last_output_directory = None
        self.is_topmost = False

        self.root.title(self.tr("window_title"))
        self.root.geometry("560x570")
        self.root.resizable(False, False)
        apply_window_icon(self.root)

        self.title_label = ctk.CTkLabel(
            root,
            text=self.tr("app_title"),
            font=ctk.CTkFont("Segoe UI", 28, "bold"),
        )
        self.title_label.pack(anchor="w", padx=30, pady=(28, 8))

        self.subtitle_label = ctk.CTkLabel(
            root,
            text=self.tr("subtitle"),
            text_color="gray60",
        )
        self.subtitle_label.pack(anchor="w", padx=30, pady=(0, 20))

        self.language_selector = ctk.CTkSegmentedButton(
            root,
            values=["PL", "EN"],
            width=76,
            height=28,
            corner_radius=8,
            border_width=1,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            command=self.change_language,
        )
        self.language_selector.place(relx=1.0, x=-25, y=38, anchor="ne")
        self.language_selector.set("PL")

        container = ctk.CTkFrame(root, corner_radius=18)
        container.pack(fill="both", expand=True, padx=30, pady=(0, 18))

        self.content_label = ctk.CTkLabel(container, text=self.tr("qr_content"), anchor="w")
        self.content_label.pack(fill="x", padx=22, pady=(24, 8))

        self.number_entry = ctk.CTkEntry(
            container,
            height=42,
            placeholder_text=self.tr("placeholder"),
        )
        self.number_entry.pack(fill="x", padx=22, pady=(0, 18))
        self.number_entry.bind("<Return>", lambda _event: self.generate_qr())

        logo_row = ctk.CTkFrame(container, fg_color="transparent")
        logo_row.pack(fill="x", padx=22, pady=4)
        self.logo_button = ctk.CTkButton(
            logo_row,
            text=self.tr("choose_logo"),
            width=160,
            command=self.choose_logo,
        )
        self.logo_button.pack(anchor="center")
        self.logo_label = ctk.CTkLabel(
            logo_row,
            text=self.tr("no_logo"),
            text_color="gray60",
        )
        self.logo_label.pack(anchor="center", pady=(8, 0))

        self.generate_button = ctk.CTkButton(
            container,
            text=self.tr("generate"),
            height=44,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            command=self.generate_qr,
        )
        self.generate_button.pack(fill="x", padx=22, pady=(28, 12))

        folder_actions = ctk.CTkFrame(container, fg_color="transparent")
        folder_actions.pack(fill="x", padx=22, pady=(0, 20))
        self.choose_output_button = ctk.CTkButton(
            folder_actions,
            text=self.tr("choose_output"),
            height=34,
            fg_color="transparent",
            border_width=1,
            command=self.choose_output_directory,
        )
        self.choose_output_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.open_output_button = ctk.CTkButton(
            folder_actions,
            text=self.tr("open_output"),
            height=34,
            fg_color="transparent",
            border_width=1,
            command=self.open_output_directory,
        )
        self.open_output_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

        footer = ctk.CTkFrame(root, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(0, 20))

        footer_left = ctk.CTkFrame(footer, fg_color="transparent")
        footer_left.pack(side="left")
        self.pin_button = ctk.CTkButton(
            footer_left,
            text=self.pin_button_text(),
            width=110,
            height=29,
            fg_color="transparent",
            border_width=1,
            command=self.toggle_topmost,
        )
        self.pin_button.pack(pady=(0, 5))
        self.support_button = ctk.CTkButton(
            footer_left,
            text=self.tr("support"),
            width=110,
            height=29,
            fg_color="transparent",
            border_width=1,
            command=self.open_support_page,
        )
        self.support_button.pack()

        self.about_button = ctk.CTkButton(
            footer,
            text=self.tr("about"),
            width=110,
            height=29,
            fg_color="transparent",
            border_width=1,
            command=self.show_about,
        )
        self.about_button.pack(side="right", anchor="s", pady=(34, 0))

    def tr(self, key):
        return TRANSLATIONS[self.current_language][key]

    def pin_button_text(self):
        state = "ON" if self.is_topmost else "OFF"
        return f"{self.tr('pin')}: {state}"

    def change_language(self, selected_language):
        self.current_language = selected_language.lower()
        self.root.title(self.tr("window_title"))
        self.title_label.configure(text=self.tr("app_title"))
        self.subtitle_label.configure(text=self.tr("subtitle"))
        self.content_label.configure(text=self.tr("qr_content"))
        self.number_entry.configure(placeholder_text=self.tr("placeholder"))
        self.logo_button.configure(text=self.tr("choose_logo"))
        if self.logo_path is None:
            self.logo_label.configure(text=self.tr("no_logo"))
        self.generate_button.configure(text=self.tr("generate"))
        self.choose_output_button.configure(text=self.tr("choose_output"))
        self.open_output_button.configure(text=self.tr("open_output"))
        self.pin_button.configure(text=self.pin_button_text())
        self.support_button.configure(text=self.tr("support"))
        self.about_button.configure(text=self.tr("about"))

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.root.attributes("-topmost", self.is_topmost)
        self.pin_button.configure(
            text=self.pin_button_text(),
            fg_color="#1f6aa5" if self.is_topmost else "transparent",
        )

    def open_support_page(self):
        webbrowser.open(SUPPORT_URLS[self.current_language])

    def show_about(self):
        messagebox.showinfo(
            self.tr("about_title"),
            (
                f"{self.tr('name')}: {self.tr('app_name')}\n"
                f"{self.tr('version')}: {APP_VERSION}\n"
                f"{self.tr('author')}: {APP_AUTHOR}\n\n"
                f"{self.tr('description')}"
            ),
        )

    def choose_logo(self):
        path = filedialog.askopenfilename(
            title=self.tr("choose_logo_dialog"),
            filetypes=[(self.tr("image_files"), "*.png;*.jpg;*.jpeg")],
        )
        if path:
            self.logo_path = path
            self.logo_label.configure(text=os.path.basename(path), text_color="#22c55e")

    def choose_output_directory(self):
        directory = filedialog.askdirectory(
            title=self.tr("choose_output_dialog"),
            initialdir=self.selected_output_directory or os.path.expanduser("~"),
        )
        if directory:
            self.selected_output_directory = os.path.normpath(directory)
            self.last_output_directory = None

    def open_output_directory(self):
        directory = self.last_output_directory or self.selected_output_directory
        if not directory:
            messagebox.showwarning(self.tr("folder_title"), self.tr("generate_first"))
            return

        if not os.path.isdir(directory):
            messagebox.showerror(self.tr("folder_title"), self.tr("folder_missing"))
            return

        try:
            os.startfile(directory)
        except OSError as error:
            messagebox.showerror(
                self.tr("folder_title"),
                self.tr("folder_open_failed").format(error=error),
            )

    def generate_qr(self):
        try:
            number = self.number_entry.get().strip()
            if not number:
                messagebox.showerror(self.tr("input_error_title"), self.tr("input_error"))
                return

            default_filename = f"{number}.png"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[(self.tr("png_files"), "*.png")],
                initialfile=default_filename,
                initialdir=self.selected_output_directory,
                title=self.tr("save_dialog"),
            )
            if not file_path:
                return

            box_size = 10
            border_size = 1
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=box_size,
                border=border_size,
            )
            qr.add_data(number)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")

            width, height = img_qr.size
            img_qr = img_qr.crop((0, 0, width, height - border_size * box_size))
            qr_width, qr_height = img_qr.size

            if self.logo_path:
                logo = Image.open(self.logo_path)
                original_width, original_height = logo.size
                target = int(qr_width * 0.20)
                scale = target / max(original_width, original_height)
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                logo = logo.resize((new_width, new_height), resample=Image.LANCZOS)

                logo_x = (qr_width - new_width) // 2
                logo_y = (qr_height - new_height) // 2
                padding = int(new_width * 0.1)
                border_box = (
                    logo_x - padding,
                    logo_y - padding,
                    logo_x + new_width + padding,
                    logo_y + new_height + padding,
                )
                draw = ImageDraw.Draw(img_qr)
                draw.rounded_rectangle(
                    border_box,
                    radius=padding,
                    fill="white",
                    outline="black",
                    width=2,
                )

                if logo.mode in ("RGBA", "LA"):
                    img_qr.paste(logo, (logo_x, logo_y), mask=logo)
                else:
                    img_qr.paste(logo, (logo_x, logo_y))

            try:
                font_label = ImageFont.truetype("arial.ttf", 10)
            except IOError:
                font_label = ImageFont.load_default()

            label_text = "dev. Headlost"
            bounding_box = font_label.getbbox(label_text)
            label_width = bounding_box[2] - bounding_box[0]
            label_height = bounding_box[3] - bounding_box[1]

            bottom_spacing = 10
            final_height = qr_height + label_height + bottom_spacing
            final_image = Image.new("RGB", (qr_width, final_height), "white")
            final_image.paste(img_qr, (0, 0))
            final_draw = ImageDraw.Draw(final_image)
            text_x = (qr_width - label_width) // 2
            final_draw.text((text_x, qr_height), label_text, font=font_label, fill="black")

            final_image.save(file_path)
            self.last_output_directory = os.path.dirname(os.path.abspath(file_path))
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("success").format(path=file_path),
            )

        except Exception:
            error = traceback.format_exc()
            messagebox.showerror(
                self.tr("unexpected_error_title"),
                self.tr("unexpected_error").format(error=error),
            )


if __name__ == "__main__":
    root = ctk.CTk()
    app = QRCodeApp(root)
    root.mainloop()
