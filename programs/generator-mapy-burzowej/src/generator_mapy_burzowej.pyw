# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, UnidentifiedImageError
from geopy.geocoders import Nominatim
import requests
from io import BytesIO
from datetime import datetime, timedelta
import re
import os
import sys
import uuid  # do generowania unikalnego user_agent
import webbrowser
from app_common import apply_window_icon, resource_path, styled_messagebox as messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Elegancka, granatowo-złota paleta interfejsu.
COLOR_BG = "#0D1520"
COLOR_CARD = "#172231"
COLOR_ENTRY = "#0F1A28"
COLOR_BORDER = "#34465D"
COLOR_TEXT = "#F4F0E6"
COLOR_MUTED = "#93A4B8"
COLOR_ACCENT = "#C99A4A"
COLOR_ACCENT_HOVER = "#D8AD66"
COLOR_ACCENT_TEXT = "#151A20"
COLOR_SECONDARY_HOVER = "#24344A"
COLOR_SUCCESS = "#2F855A"

APP_TITLE = "Oznaczanie lokalizacji na mapie burzowej"
APP_VERSION = "5.1.0"
APP_AUTHOR = "Beniamin Żak"
APP_DESCRIPTION = "Tworzy mapę burzową z oznaczeniem wybranej lokalizacji."

SUPPORT_URLS = {
    "pl": "https://buycoffee.to/beniamin-tv6",
    "en": "https://ko-fi.com/beniaminzak",
}

TRANSLATIONS = {
    "pl": {
        "window_title": "Oznaczanie lokalizacji na mapie burzowej",
        "title": "Mapa burzowa",
        "description": "Tworzy mapę burzową z oznaczeniem wybranej lokalizacji.",
        "postal": "Kod / współrzędne",
        "place": "Miasto / adres",
        "place_placeholder": "Miasto, ulica lub pełny adres",
        "date": "Data",
        "date_placeholder": "dd.mm.rrrr lub rrrr-mm-dd",
        "output_file": "Plik wynikowy",
        "output_placeholder": "Wybierz miejsce zapisu",
        "choose_output": "Miejsce zapisu",
        "preview": "Podgląd mapy pojawi się tutaj",
        "pin": "Przypnij",
        "support": "Wsparcie  ♥",
        "create": "Utwórz mapę",
        "open_folder": "Otwórz folder zapisu",
        "about": "O mnie",
        "about_title": "O programie",
        "name": "Nazwa",
        "version": "Wersja",
        "author": "Autor",
        "download_error": "Błąd przy pobieraniu mapy: {error}",
        "invalid_image": "Otrzymano nieprawidłowy obraz.",
        "date_unavailable_title": "Data jeszcze niedostępna",
        "date_unavailable": "Mapa dla dzisiejszej lub przyszłej daty nie jest jeszcze dostępna.\n\nWybierz datę najpóźniej z dnia wczorajszego: {date}.",
        "folder_title": "Folder zapisu",
        "folder_first": "Najpierw wybierz miejsce zapisu lub utwórz mapę.",
        "folder_open_error": "Nie można otworzyć folderu:\n{error}",
        "missing_data": "Brak danych",
        "location_date_required": "Podaj lokalizację (kod, miasto, adres lub współrzędne) oraz datę.",
        "date_error": "Błąd daty",
        "date_formats": "Obsługiwane są m.in. formaty dd.mm.rrrr, rrrr-mm-dd, dd/mm/rrrr i dd-mm-rrrr.",
        "save_title": "Wybierz miejsce zapisu mapy",
        "all_required": "Podaj lokalizację, datę oraz plik wynikowy.",
        "pin_missing": "Brak pinezki",
        "pin_file_missing": "Nie znaleziono pliku: {path}",
        "date_format_error": "Błąd formatu daty",
        "date_unrecognized": "Nie udało się rozpoznać podanej daty.",
        "map_download_error": "Błąd pobierania mapy",
        "geocoding_error": "Błąd geokodowania",
        "location_not_found": "Nie znaleziono lokalizacji. Spróbuj podać kod pocztowy, miasto, pełny adres albo współrzędne.",
        "save_error": "Błąd zapisu",
        "success": "Sukces",
        "saved_as": "Zapisano jako:\n{path}",
    },
    "en": {
        "window_title": "Storm Map Location Marker",
        "title": "Storm map",
        "description": "Creates a storm map marking the selected location.",
        "postal": "Postal code / coordinates",
        "place": "City / address",
        "place_placeholder": "City, street, or full address",
        "date": "Date",
        "date_placeholder": "dd.mm.yyyy or yyyy-mm-dd",
        "output_file": "Output file",
        "output_placeholder": "Choose an output location",
        "choose_output": "Choose output",
        "preview": "The map preview will appear here",
        "pin": "Pin",
        "support": "Support  ♥",
        "create": "Create map",
        "open_folder": "Open output folder",
        "about": "About",
        "about_title": "About",
        "name": "Name",
        "version": "Version",
        "author": "Author",
        "download_error": "Could not download the map: {error}",
        "invalid_image": "The server returned an invalid image.",
        "date_unavailable_title": "Date not available yet",
        "date_unavailable": "The map for today or a future date is not available yet.\n\nChoose yesterday or an earlier date: {date}.",
        "folder_title": "Output folder",
        "folder_first": "Choose an output location or create a map first.",
        "folder_open_error": "Could not open the folder:\n{error}",
        "missing_data": "Missing information",
        "location_date_required": "Enter a location (postal code, city, address, or coordinates) and a date.",
        "date_error": "Date error",
        "date_formats": "Supported formats include dd.mm.yyyy, yyyy-mm-dd, dd/mm/yyyy, and dd-mm-yyyy.",
        "save_title": "Choose where to save the map",
        "all_required": "Enter a location, date, and output file.",
        "pin_missing": "Marker missing",
        "pin_file_missing": "File not found: {path}",
        "date_format_error": "Date format error",
        "date_unrecognized": "The entered date could not be recognized.",
        "map_download_error": "Map download error",
        "geocoding_error": "Geocoding error",
        "location_not_found": "Location not found. Try a postal code, city, full address, or coordinates.",
        "save_error": "Save error",
        "success": "Success",
        "saved_as": "Saved as:\n{path}",
    },
}

current_language = "pl"


def tr(key):
    return TRANSLATIONS[current_language][key]


# --- Funkcje pomocnicze ---

def latlon_na_piksele(lat, lon, lat_min, lat_max, lon_min, lon_max, szerokosc, wysokosc):
    x = int((lon - lon_min) / (lon_max - lon_min) * szerokosc)
    y = int((lat_max - lat) / (lat_max - lat_min) * wysokosc)
    return x, y

def pobierz_mape(data_formatted):
    url = f"https://burzowo.info/render?map=5&date={data_formatted}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except requests.RequestException as e:
        raise RuntimeError(tr("download_error").format(error=e))
    except UnidentifiedImageError:
        raise RuntimeError(tr("invalid_image"))


def parse_date(value):
    value = re.sub(r"\s+", " ", value.strip())
    formats = (
        "%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d",
        "%d %m %Y", "%d.%m.%y", "%d-%m-%y", "%d/%m/%y",
    )
    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    raise ValueError("Nie rozpoznano daty")


class DateNotAvailableError(ValueError):
    def __init__(self, latest_available):
        super().__init__("Mapa dla tej daty nie jest jeszcze dostępna")
        self.latest_available = latest_available


def parse_available_map_date(value):
    """Akceptuje wyłącznie daty, dla których mapa powinna już istnieć."""
    selected_date = parse_date(value)
    latest_available = datetime.now().date() - timedelta(days=1)
    if selected_date.date() > latest_available:
        raise DateNotAvailableError(latest_available)
    return selected_date


def show_date_not_available(error):
    messagebox.showwarning(
        tr("date_unavailable_title"),
        tr("date_unavailable").format(date=f"{error.latest_available:%d.%m.%Y}"),
    )


def normalize_postal_code(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 5:
        return f"{digits[:2]}-{digits[2:]}"
    match = re.search(r"\b\d{2}\s*[- ]?\s*\d{3}\b", value or "")
    if match:
        digits = re.sub(r"\D", "", match.group(0))
        return f"{digits[:2]}-{digits[2:]}"
    return (value or "").strip()


def parse_coordinates(value):
    match = re.fullmatch(
        r"\s*([+-]?\d{1,2}(?:[.,]\d+)?)\s*[,; ]\s*([+-]?\d{1,3}(?:[.,]\d+)?)\s*",
        value or "",
    )
    if not match:
        return None
    lat = float(match.group(1).replace(",", "."))
    lon = float(match.group(2).replace(",", "."))
    if 49.0 <= lat <= 55.2 and 14.0 <= lon <= 24.5:
        return lat, lon
    return None


def find_location(postal_value, place_value):
    coordinate_value = parse_coordinates(place_value) or parse_coordinates(postal_value)
    if coordinate_value:
        return coordinate_value

    postal_code = normalize_postal_code(postal_value)
    place = re.sub(r"\s+", " ", place_value.strip())
    geocoder = Nominatim(user_agent=f"storm-map-beniamin-{uuid.uuid4()}", timeout=12)
    queries = []
    if postal_code and place:
        queries.extend([
            {"postalcode": postal_code, "city": place, "country": "Polska"},
            f"{place}, {postal_code}, Polska",
            f"{postal_code} {place}, Polska",
        ])
    if place:
        queries.extend([f"{place}, Polska", place])
    if postal_code:
        queries.extend([f"{postal_code}, Polska", postal_code])

    seen = set()
    for query in queries:
        key = str(query).casefold()
        if key in seen:
            continue
        seen.add(key)
        try:
            location = geocoder.geocode(query, country_codes="pl", exactly_one=True, addressdetails=True)
        except Exception:
            continue
        if location and 49.0 <= location.latitude <= 55.2 and 14.0 <= location.longitude <= 24.5:
            return location.latitude, location.longitude
    return None

# Ścieżka do domyślnej pinezki (plik obok skryptu)
DEFAULT_PINEZKA = str(resource_path("pinezka.png"))

# --- Akcje GUI ---

def about():
    messagebox.showinfo(
        tr("about_title"),
        f"{tr('name')}: {tr('window_title')}\n{tr('version')}: {APP_VERSION}\n"
        f"{tr('author')}: {APP_AUTHOR}\n\n{tr('description')}",
    )


def open_support():
    webbrowser.open(SUPPORT_URLS[current_language])


last_saved_path = None


def open_output_folder():
    candidate = pole_zapis.get().strip() or last_saved_path
    folder = os.path.dirname(os.path.abspath(candidate)) if candidate else ""
    if not folder or not os.path.isdir(folder):
        messagebox.showwarning(tr("folder_title"), tr("folder_first"))
        return
    try:
        os.startfile(folder)
    except OSError as exc:
        messagebox.showerror(tr("folder_title"), tr("folder_open_error").format(error=exc))

topmost_enabled = False
def toggle_topmost():
    global topmost_enabled
    topmost_enabled = not topmost_enabled
    root.attributes('-topmost', topmost_enabled)
    status = 'ON' if topmost_enabled else 'OFF'
    btn_top.configure(text=f"{tr('pin')}: {status}",
                      fg_color=COLOR_SUCCESS if topmost_enabled else "transparent")


def utworz_nazwe_pliku(kod, miasto, data_input, extension=".png"):
    """Buduje nazwę pliku na podstawie aktualnych danych formularza."""
    data_plik = parse_date(data_input).strftime("%Y%m%d")

    def clean(value):
        value = re.sub(r'[\\/*?:"<>|]', "", value.strip())
        return re.sub(r"\s+", " ", value).rstrip(". ")

    parts = ["mapa", data_plik]
    parts.extend(part for part in (clean(kod), clean(miasto)) if part)
    return "_".join(parts) + extension


def aktualizuj_nazwe_pliku(*_):
    """Zachowuje wybrany folder, ale synchronizuje nazwę z formularzem."""
    current_path = pole_zapis.get().strip()
    if not current_path:
        return

    extension = os.path.splitext(current_path)[1].lower()
    if extension not in (".png", ".jpg", ".jpeg"):
        extension = ".png"

    try:
        filename = utworz_nazwe_pliku(
            pole_kod.get(), pole_miasto.get(), pole_data.get(), extension
        )
    except ValueError:
        return

    updated_path = os.path.join(os.path.dirname(current_path), filename)
    if updated_path != current_path:
        pole_zapis.delete(0, tk.END)
        pole_zapis.insert(0, updated_path)


def zaplanuj_aktualizacje_nazwy(_event=None):
    """Aktualizuje nazwę po zakończeniu obsługi klawisza lub wklejania."""
    root.after_idle(aktualizuj_nazwe_pliku)


def wybierz_miejsce_zapisu():
    kod = pole_kod.get().strip()
    miasto = pole_miasto.get().strip()
    data_input = pole_data.get().strip()

    if not (kod or miasto) or not data_input:
        messagebox.showwarning(tr("missing_data"), tr("location_date_required"))
        return

    try:
        parse_available_map_date(data_input)
        default_name = utworz_nazwe_pliku(kod, miasto, data_input)
    except DateNotAvailableError as error:
        show_date_not_available(error)
        return
    except ValueError:
        messagebox.showerror(tr("date_error"), tr("date_formats"))
        return

    save_path = filedialog.asksaveasfilename(
        title=tr("save_title"),
        defaultextension=".png",
        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg")],
        initialfile=default_name
    )
    if save_path:
        pole_zapis.delete(0, tk.END)
        pole_zapis.insert(0, save_path)

def wykonaj():
    global obraz_mapy, obraz_tk, last_saved_path

    kod = pole_kod.get().strip()
    miasto = pole_miasto.get().strip()
    data_input = pole_data.get().strip()
    save_path = pole_zapis.get().strip()

    if not (kod or miasto) or not data_input or not save_path:
        messagebox.showwarning(tr("missing_data"), tr("all_required"))
        return
    if not os.path.exists(DEFAULT_PINEZKA):
        messagebox.showwarning(tr("pin_missing"), tr("pin_file_missing").format(path=DEFAULT_PINEZKA))
        return

    # Parsowanie daty
    try:
        dp = parse_available_map_date(data_input)
        df = dp.strftime('%Y%m%d')
    except DateNotAvailableError as error:
        show_date_not_available(error)
        return
    except ValueError:
        messagebox.showerror(tr("date_format_error"), tr("date_unrecognized"))
        return

    # Pobranie mapy
    try:
        obraz_mapy = pobierz_mape(df)
    except RuntimeError as e:
        messagebox.showerror(tr("map_download_error"), str(e))
        return

    # Geokodowanie
    location = find_location(kod, miasto)
    if not location:
        messagebox.showerror(
            tr("geocoding_error"),
            tr("location_not_found"),
        )
        return

    # Wklejenie pinezki
    latitude, longitude = location
    x, y = latlon_na_piksele(latitude, longitude,
                             49.0, 55.2, 14.0, 24.5,
                             *obraz_mapy.size)
    pine = Image.open(DEFAULT_PINEZKA).convert("RGBA")
    pine = pine.resize((int(pine.width*0.1), int(pine.height*0.1)), Image.LANCZOS)
    obraz_mapy.paste(pine, (x-pine.width//2, y-pine.height), pine)

    # Zapis pliku
    if not save_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        save_path += '.png'
    try:
        obraz_mapy.save(save_path)
        last_saved_path = save_path
        btn_open_folder.configure(state="normal")
    except Exception as e:
        messagebox.showerror(tr("save_error"), str(e))
        return

    # Wyświetlenie
    podglad = obraz_mapy.copy()
    podglad.thumbnail((560, 400), Image.LANCZOS)
    obraz_tk = ctk.CTkImage(light_image=podglad, dark_image=podglad, size=podglad.size)
    etykieta_obraz.configure(image=obraz_tk, text="")

    messagebox.showinfo(tr("success"), tr("saved_as").format(path=save_path))

# --- Budowa GUI ---

root = ctk.CTk()
root.title(tr("window_title"))
root.geometry("760x830")
root.resizable(False, False)
root.configure(fg_color=COLOR_BG)
apply_window_icon(root)


def change_language(selected_language):
    global current_language

    current_language = selected_language.lower()
    root.title(tr("window_title"))
    title_label.configure(text=tr("title"))
    postal_label.configure(text=tr("postal"))
    place_label.configure(text=tr("place"))
    pole_miasto.configure(placeholder_text=tr("place_placeholder"))
    date_label.configure(text=tr("date"))
    pole_data.configure(placeholder_text=tr("date_placeholder"))
    output_label.configure(text=tr("output_file"))
    pole_zapis.configure(placeholder_text=tr("output_placeholder"))
    btn_save.configure(text=tr("choose_output"))
    if etykieta_obraz.cget("text"):
        etykieta_obraz.configure(text=tr("preview"))
    btn_top.configure(text=f"{tr('pin')}: {'ON' if topmost_enabled else 'OFF'}")
    support_button.configure(text=tr("support"))
    btn_wykonaj.configure(text=tr("create"))
    btn_open_folder.configure(text=tr("open_folder"))
    about_button.configure(text=tr("about"))

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(2, weight=1)

title_label = ctk.CTkLabel(
    root,
    text=tr("title"),
    font=ctk.CTkFont("Segoe UI", 28, "bold"),
    text_color=COLOR_TEXT,
)
title_label.grid(row=0, column=0, padx=28, pady=(24, 12), sticky="w")

formularz = ctk.CTkFrame(root, corner_radius=18, fg_color=COLOR_CARD)
formularz.grid(row=1, column=0, padx=28, pady=8, sticky="ew")
formularz.grid_columnconfigure(1, weight=1)

postal_label = ctk.CTkLabel(formularz, text=tr("postal"), text_color=COLOR_TEXT)
postal_label.grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")
pole_kod = ctk.CTkEntry(formularz, placeholder_text="00-000 lub 52.23, 21.01", fg_color=COLOR_ENTRY, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
pole_kod.grid(row=0, column=1, padx=18, pady=(18, 8), sticky="ew")
place_label = ctk.CTkLabel(formularz, text=tr("place"), text_color=COLOR_TEXT)
place_label.grid(row=1, column=0, padx=18, pady=8, sticky="w")
pole_miasto = ctk.CTkEntry(formularz, placeholder_text=tr("place_placeholder"), fg_color=COLOR_ENTRY, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
pole_miasto.grid(row=1, column=1, padx=18, pady=8, sticky="ew")
date_label = ctk.CTkLabel(formularz, text=tr("date"), text_color=COLOR_TEXT)
date_label.grid(row=2, column=0, padx=18, pady=8, sticky="w")
pole_data = ctk.CTkEntry(formularz, placeholder_text=tr("date_placeholder"), fg_color=COLOR_ENTRY, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
pole_data.grid(row=2, column=1, padx=18, pady=8, sticky="ew")
output_label = ctk.CTkLabel(formularz, text=tr("output_file"), text_color=COLOR_TEXT)
output_label.grid(row=3, column=0, padx=18, pady=(8, 18), sticky="w")
pole_zapis = ctk.CTkEntry(formularz, placeholder_text=tr("output_placeholder"), fg_color=COLOR_ENTRY, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
pole_zapis.grid(row=3, column=1, padx=(18, 8), pady=(8, 18), sticky="ew")
btn_save = ctk.CTkButton(
    formularz, text=tr("choose_output"), width=116, height=28,
    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
    text_color=COLOR_ACCENT_TEXT, command=wybierz_miejsce_zapisu,
)
btn_save.grid(row=3, column=2, padx=(0, 18), pady=(8, 18))

for input_field in (pole_kod, pole_miasto, pole_data):
    input_field.bind("<KeyRelease>", zaplanuj_aktualizacje_nazwy)
    input_field.bind("<<Paste>>", zaplanuj_aktualizacje_nazwy)
    input_field.bind("<<Cut>>", zaplanuj_aktualizacje_nazwy)
    input_field.bind("<FocusOut>", zaplanuj_aktualizacje_nazwy)

podglad_frame = ctk.CTkFrame(root, corner_radius=18, fg_color=COLOR_CARD)
podglad_frame.grid(row=2, column=0, padx=28, pady=12, sticky="nsew")
podglad_frame.grid_columnconfigure(0, weight=1)
podglad_frame.grid_rowconfigure(0, weight=1)
etykieta_obraz = ctk.CTkLabel(podglad_frame, text=tr("preview"), text_color=COLOR_MUTED)
etykieta_obraz.grid(row=0, column=0, padx=18, pady=18)

akcje = ctk.CTkFrame(root, fg_color="transparent")
akcje.grid(row=3, column=0, padx=28, pady=(2, 20), sticky="ew")
for column in range(3):
    akcje.grid_columnconfigure(column, weight=1, uniform="action_columns")

secondary_button = {
    "height": 28,
    "fg_color": "transparent",
    "hover_color": COLOR_SECONDARY_HOVER,
    "border_width": 1,
    "border_color": COLOR_BORDER,
    "text_color": COLOR_TEXT,
}

btn_top = ctk.CTkButton(
    akcje, text=f"{tr('pin')}: OFF", width=110,
    command=toggle_topmost, **secondary_button,
)
btn_top.grid(row=0, column=0, pady=(0, 7), sticky="w")

support_button = ctk.CTkButton(
    akcje, text=tr("support"), width=110,
    command=open_support, **secondary_button,
)
support_button.grid(row=1, column=0, sticky="w")

btn_wykonaj = ctk.CTkButton(
    akcje, text=tr("create"), width=170, height=30,
    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
    text_color=COLOR_ACCENT_TEXT, command=wykonaj,
)
btn_wykonaj.grid(row=0, column=1, pady=(0, 7))

btn_open_folder = ctk.CTkButton(
    akcje, text=tr("open_folder"), width=170,
    command=open_output_folder, **secondary_button,
)
btn_open_folder.grid(row=1, column=1)

about_button = ctk.CTkButton(
    akcje, text=tr("about"), width=110,
    command=about, **secondary_button,
)
about_button.grid(row=1, column=2, sticky="e")

language_selector = ctk.CTkSegmentedButton(
    root,
    values=["PL", "EN"],
    width=76,
    height=28,
    corner_radius=8,
    border_width=1,
    fg_color=COLOR_ENTRY,
    selected_color=COLOR_ACCENT,
    selected_hover_color=COLOR_ACCENT_HOVER,
    unselected_color=COLOR_ENTRY,
    unselected_hover_color=COLOR_SECONDARY_HOVER,
    text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 10, "bold"),
    command=change_language,
)
language_selector.place(relx=1.0, x=-28, y=28, anchor="ne")
language_selector.set("PL")

root.mainloop()
