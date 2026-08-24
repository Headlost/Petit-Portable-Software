# -*- coding: utf-8 -*-
"""
Program: Rozpoznaj województwo po kodzie pocztowym
Wersja: 2.6.0
Autor: Beniamin Żak (zmodyfikowany)
"""

import tkinter as tk
import customtkinter as ctk
import threading
import re
import os
import sys
import unicodedata
import webbrowser
import pgeocode
import pandas as pd
from geopy.geocoders import Nominatim
from app_common import apply_window_icon, styled_messagebox as messagebox

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_TITLE = "Rozpoznawanie województw"
APP_VERSION = "2.6.0"
APP_AUTHOR = "Beniamin Żak"
APP_DESCRIPTION = "Rozpoznaje jedno lub wiele województw na podstawie kodów, miast i adresów."

SUPPORT_URLS = {
    "pl": "https://buycoffee.to/beniamin-tv6",
    "en": "https://ko-fi.com/beniaminzak",
}

TRANSLATIONS = {
    "pl": {
        "window_title": "Rozpoznawanie województw",
        "title": "Rozpoznaj województwa",
        "subtitle": "Wklej kody, miasta, ulice, adresy lub większy blok tekstu",
        "description": "Rozpoznaje jedno lub wiele województw na podstawie kodów, miast i adresów.",
        "source": "Tekst źródłowy",
        "source_placeholder": "Wklej dowolny fragment tekstu, np. całą wiadomość e-mail. Jeśli tekst zawiera kod pocztowy, województwo zostanie rozpoznane automatycznie.",
        "detect": "Wykryj województwa",
        "analyzing": "Analizuję lokalizacje…",
        "result": "Wynik",
        "pin": "Przypnij",
        "support": "Wsparcie  ♥",
        "about": "O mnie",
        "about_title": "O programie",
        "name": "Nazwa",
        "version": "Wersja",
        "author": "Autor",
        "missing_title": "Brak danych",
        "missing_text": "Wklej kod pocztowy, miasto, ulicę, adres lub większy blok tekstu.",
        "no_results_title": "Brak wyników",
        "no_results": "Nie rozpoznano województwa. Dodaj miasto, kod pocztowy albo pełniejszy adres.",
        "unexpected_error": "Niespodziewany błąd",
    },
    "en": {
        "window_title": "Voivodeship Recognition",
        "title": "Recognize voivodeships",
        "subtitle": "Paste postal codes, cities, streets, addresses, or a larger block of text",
        "description": "Recognizes one or more Polish voivodeships from postal codes, cities, and addresses.",
        "source": "Source text",
        "source_placeholder": "Paste any text, such as an entire email. If it contains a postal code, the voivodeship will be recognized automatically.",
        "detect": "Detect voivodeships",
        "analyzing": "Analyzing locations…",
        "result": "Result",
        "pin": "Pin",
        "support": "Support  ♥",
        "about": "About",
        "about_title": "About",
        "name": "Name",
        "version": "Version",
        "author": "Author",
        "missing_title": "Missing information",
        "missing_text": "Paste a postal code, city, street, address, or a larger block of text.",
        "no_results_title": "No results",
        "no_results": "No voivodeship was recognized. Add a city, postal code, or fuller address.",
        "unexpected_error": "Unexpected error",
    },
}

current_language = "pl"
last_detected_states = set()
input_placeholder_active = False


def tr(key):
    return TRANSLATIONS[current_language][key]


# --- CONSTANTS ---
BG_COLOR     = "#FFDAB9"
FONT_LABEL   = ("Arial", 10)
FONT_INPUT   = ("Arial", 11)
FONT_OUTPUT  = ("Arial", 12)

# regex do kodu pocztowego XX-XXX
POSTAL_REGEX = re.compile(r"\b(\d{2})\s*[- ]?\s*(\d{3})\b")

# mapowanie angielskich nazw na polskie przymiotnikowe,
# włącznie z synonimami bez „Voivodeship”
VOIVODESHIP_MAP = {
    "Lower Silesian Voivodeship":     "Dolnośląskie",
    "Lower Silesian":                  "Dolnośląskie",
    "Kuyavian-Pomeranian Voivodeship": "Kujawsko-Pomorskie",
    "Kuyavian-Pomeranian":             "Kujawsko-Pomorskie",
    "Lublin Voivodeship":             "Lubelskie",
    "Lublin":                          "Lubelskie",
    "Lubusz Voivodeship":             "Lubuskie",
    "Lubusz":                          "Lubuskie",
    "Łódź Voivodeship":               "Łódzkie",
    "Łódź":                            "Łódzkie",
    "Lesser Poland Voivodeship":      "Małopolskie",
    "Lesser Poland":                  "Małopolskie",
    "Masovian Voivodeship":           "Mazowieckie",
    "Masovian":                        "Mazowieckie",
    "Opole Voivodeship":              "Opolskie",
    "Opole":                           "Opolskie",
    "Podlaskie Voivodeship":          "Podlaskie",
    "Podlaskie":                       "Podlaskie",
    "Pomeranian Voivodeship":         "Pomorskie",
    "Pomeranian":                      "Pomorskie",
    "Silesian Voivodeship":           "Śląskie",
    "Silesia":                         "Śląskie",
    "Subcarpathian Voivodeship":      "Podkarpackie",
    "Subcarpathian":                   "Podkarpackie",
    "Świętokrzyskie Voivodeship":     "Świętokrzyskie",
    "Świętokrzyskie":                  "Świętokrzyskie",
    "Warmian-Masurian Voivodeship":   "Warmińsko-Mazurskie",
    "Warmian-Masurian":                "Warmińsko-Mazurskie",
    "Greater Poland Voivodeship":     "Wielkopolskie",
    "Greater Poland":                  "Wielkopolskie",
    "West Pomeranian Voivodeship":    "Zachodniopomorskie",
    "West Pomeranian":                 "Zachodniopomorskie",
}

# inicjalizacja bazy kodów pocztowych
nom = pgeocode.Nominatim('PL')
geo = Nominatim(user_agent="voivodeship-recognizer-beniamin", timeout=3)
place_index = None

ISO_STATE_MAP = {
    "PL-02": "Dolnośląskie", "PL-04": "Kujawsko-Pomorskie", "PL-06": "Lubelskie",
    "PL-08": "Lubuskie", "PL-10": "Łódzkie", "PL-12": "Małopolskie",
    "PL-14": "Mazowieckie", "PL-16": "Opolskie", "PL-18": "Podkarpackie",
    "PL-20": "Podlaskie", "PL-22": "Pomorskie", "PL-24": "Śląskie",
    "PL-26": "Świętokrzyskie", "PL-28": "Warmińsko-Mazurskie",
    "PL-30": "Wielkopolskie", "PL-32": "Zachodniopomorskie",
}
STATE_ORDER = list(ISO_STATE_MAP.values())
STATE_NAMES_EN = {
    "Dolnośląskie": "Lower Silesian",
    "Kujawsko-Pomorskie": "Kuyavian-Pomeranian",
    "Lubelskie": "Lublin",
    "Lubuskie": "Lubusz",
    "Łódzkie": "Łódź",
    "Małopolskie": "Lesser Poland",
    "Mazowieckie": "Masovian",
    "Opolskie": "Opole",
    "Podkarpackie": "Subcarpathian",
    "Podlaskie": "Podlaskie",
    "Pomorskie": "Pomeranian",
    "Śląskie": "Silesian",
    "Świętokrzyskie": "Świętokrzyskie",
    "Warmińsko-Mazurskie": "Warmian-Masurian",
    "Wielkopolskie": "Greater Poland",
    "Zachodniopomorskie": "West Pomeranian",
}


def normalize_text(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", " ", value.casefold())
    return re.sub(r"\s+", " ", value).strip()


STATE_ALIASES = {}
for source, target in VOIVODESHIP_MAP.items():
    STATE_ALIASES[normalize_text(source).replace(" voivodeship", "")] = target
for state in STATE_ORDER:
    STATE_ALIASES[normalize_text(state)] = state


def normalize_state(value):
    key = normalize_text(value)
    key = re.sub(r"\b(wojewodztwo|voivodeship)\b", "", key).strip()
    if key in STATE_ALIASES:
        return STATE_ALIASES[key]
    for alias, state in STATE_ALIASES.items():
        if alias and (alias in key or key in alias):
            return state
    return None


def get_place_index():
    global place_index
    if place_index is not None:
        return place_index
    index = {}
    data = getattr(nom, "_data", None)
    if isinstance(data, pd.DataFrame):
        for row in data[["place_name", "state_name"]].dropna().itertuples(index=False):
            state = normalize_state(row.state_name)
            if not state:
                continue
            for place in re.split(r"[,;/]", str(row.place_name)):
                key = normalize_text(place)
                if len(key) >= 3:
                    index.setdefault(key, set()).add(state)
    place_index = index
    return place_index


def normalize_info(info):
    """Zwraca dict {'state_name', 'place_name'} lub None."""
    if info is None:
        return None
    if isinstance(info, pd.DataFrame):
        if info.empty:
            return None
        row = info.iloc[0]
        return {"state_name": row.state_name, "place_name": row.place_name}
    if isinstance(info, pd.Series):
        return {"state_name": info.get("state_name"), "place_name": info.get("place_name")}
    if isinstance(info, dict):
        return {"state_name": info.get("state_name"), "place_name": info.get("place_name")}
    return None


def clear_output():
    output_entry.configure(state='normal')
    output_entry.delete("1.0", tk.END)
    output_entry.configure(state='disabled')


def show_input_placeholder(_event=None):
    global input_placeholder_active

    if text_input.get("1.0", "end").strip() and not input_placeholder_active:
        return
    text_input.delete("1.0", tk.END)
    text_input.insert("1.0", tr("source_placeholder"))
    text_input.configure(text_color=("gray55", "gray55"))
    input_placeholder_active = True


def clear_input_placeholder(_event=None):
    global input_placeholder_active

    if not input_placeholder_active:
        return
    text_input.delete("1.0", tk.END)
    text_input.configure(text_color=("gray10", "gray90"))
    input_placeholder_active = False


def restore_input_placeholder(_event=None):
    if not text_input.get("1.0", "end").strip():
        show_input_placeholder()


def show_about():
    messagebox.showinfo(
        tr("about_title"),
        f"{tr('name')}: {tr('window_title')}\n{tr('version')}: {APP_VERSION}\n"
        f"{tr('author')}: {APP_AUTHOR}\n\n{tr('description')}",
    )


def open_support():
    webbrowser.open(SUPPORT_URLS[current_language])


def toggle_topmost():
    global is_topmost
    is_topmost = not is_topmost
    root.attributes('-topmost', is_topmost)
    top_btn.configure(
        text=f"{tr('pin')}: {'ON' if is_topmost else 'OFF'}",
        fg_color="#16a34a" if is_topmost else "transparent",
    )


def detect_voivodeship():
    """Uruchamia analizę w tle, aby nie blokować GUI."""
    text = "" if input_placeholder_active else text_input.get("1.0", "end").strip()
    clear_output()
    if not text:
        messagebox.showwarning(tr("missing_title"), tr("missing_text"))
        return
    btn.configure(state="disabled", text=tr("analyzing"))
    threading.Thread(target=_worker_detect, args=(text,), daemon=True).start()


def states_from_postal_codes(text):
    states = set()
    for prefix, suffix in POSTAL_REGEX.findall(text):
        code = f"{prefix}-{suffix}"
        try:
            data = normalize_info(nom.query_postal_code(code))
        except Exception:
            continue
        state = normalize_state(data.get("state_name") if data else None)
        if state:
            states.add(state)
    return states


def states_from_place_names(text):
    states = set()
    index = get_place_index()
    for fragment in re.split(r"[\n;,|]+|\s+oraz\s+|\s+i\s+", text, flags=re.IGNORECASE):
        candidate = normalize_text(fragment.rsplit(":", 1)[-1])
        matches = index.get(candidate, set())
        if len(matches) == 1:
            states.update(matches)
    return states


def geocoding_candidates(text):
    candidates = []
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= 280:
        candidates.append(compact)
    for part in re.split(r"[\n;|]+|\s+oraz\s+|\s+i\s+|,(?=\s*[A-ZĄĆĘŁŃÓŚŹŻ])", text, flags=re.IGNORECASE):
        part = re.sub(r"\s+", " ", part).strip(" ,.-")
        if re.match(r"^(ul\.?|ulica|al\.?|aleja|pl\.?|plac|os\.?|osiedle)\s", part, re.IGNORECASE):
            continue
        if 3 <= len(part) <= 220:
            candidates.append(part)
    return list(dict.fromkeys(candidates))[:4]


def geocode_with_deadline(query, seconds=3.5):
    """Nie pozwala, by problem z DNS lub siecią blokował analizę bez końca."""
    result = []

    def request():
        try:
            result.append(geo.geocode(
                query,
                exactly_one=True,
                country_codes="pl",
                addressdetails=True,
                timeout=3,
            ))
        except Exception:
            result.append(None)

    worker = threading.Thread(target=request, daemon=True)
    worker.start()
    worker.join(seconds)
    return result[0] if result else None


def states_from_geocoding(text):
    states = set()
    for query in geocoding_candidates(text):
        location = geocode_with_deadline(query)
        if location:
            address = location.raw.get("address", {})
            state = normalize_state(address.get("state"))
            if not state:
                for key, value in {**location.raw, **address}.items():
                    if str(key).startswith("ISO3166-2") and value in ISO_STATE_MAP:
                        state = ISO_STATE_MAP[value]
                        break
            if state:
                states.add(state)
    return states


def update_results(states):
    global last_detected_states

    last_detected_states = set(states)
    btn.configure(state="normal", text=tr("detect"))
    output_entry.configure(state="normal")
    output_entry.delete("1.0", tk.END)
    if states:
        ordered = sorted(states, key=lambda item: STATE_ORDER.index(item) if item in STATE_ORDER else 99)
        displayed = [STATE_NAMES_EN.get(state, state) if current_language == "en" else state for state in ordered]
        output_entry.insert("1.0", "\n".join(f"• {state}" for state in displayed))
    output_entry.configure(state="disabled")


def _worker_detect(text):
    try:
        states = set()
        states.update(states_from_postal_codes(text))
        geocoded_states = states_from_geocoding(text)
        states.update(geocoded_states)
        if not geocoded_states:
            states.update(states_from_place_names(text))
        root.after(0, lambda result=states: update_results(result))
        if not states:
            root.after(0, lambda: messagebox.showwarning(
                tr("no_results_title"),
                tr("no_results"),
            ))
    except Exception as exc:
        root.after(0, lambda error=str(exc): (
            btn.configure(state="normal", text=tr("detect")),
            messagebox.showerror(tr("unexpected_error"), error),
        ))


# --- Budowa GUI ---
root = ctk.CTk()
root.title(tr("window_title"))
root.geometry("650x680")
root.resizable(False, False)
apply_window_icon(root)
is_topmost = False


def change_language(selected_language):
    global current_language

    current_language = selected_language.lower()
    root.title(tr("window_title"))
    title_label.configure(text=tr("title"))
    subtitle_label.configure(text=tr("subtitle"))
    source_label.configure(text=tr("source"))
    if input_placeholder_active:
        show_input_placeholder()
    if str(btn.cget("state")) == "disabled":
        btn.configure(text=tr("analyzing"))
    else:
        btn.configure(text=tr("detect"))
    result_label.configure(text=tr("result"))
    top_btn.configure(text=f"{tr('pin')}: {'ON' if is_topmost else 'OFF'}")
    support_button.configure(text=tr("support"))
    about_button.configure(text=tr("about"))
    if last_detected_states:
        ordered = sorted(
            last_detected_states,
            key=lambda item: STATE_ORDER.index(item) if item in STATE_ORDER else 99,
        )
        displayed = [
            STATE_NAMES_EN.get(state, state) if current_language == "en" else state
            for state in ordered
        ]
        output_entry.configure(state="normal")
        output_entry.delete("1.0", tk.END)
        output_entry.insert("1.0", "\n".join(f"• {state}" for state in displayed))
        output_entry.configure(state="disabled")

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(2, weight=1)

title_label = ctk.CTkLabel(
    root, text=tr("title"), font=ctk.CTkFont("Segoe UI", 28, "bold")
)
title_label.grid(row=0, column=0, padx=30, pady=(28, 8), sticky="w")
subtitle_label = ctk.CTkLabel(root, text=tr("subtitle"), text_color="gray60")
subtitle_label.grid(row=1, column=0, padx=30, pady=(0, 18), sticky="w")

main_frame = ctk.CTkFrame(root, corner_radius=18)
main_frame.grid(row=2, column=0, padx=30, pady=(0, 16), sticky="nsew")
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(1, weight=1)

source_label = ctk.CTkLabel(main_frame, text=tr("source"))
source_label.grid(row=0, column=0, padx=22, pady=(20, 8), sticky="w")
text_input = ctk.CTkTextbox(
    main_frame,
    height=170,
    corner_radius=12,
    font=FONT_INPUT,
    wrap="word",
)
text_input.grid(row=1, column=0, padx=22, pady=(0, 14), sticky="nsew")
text_input.bind("<FocusIn>", clear_input_placeholder, add="+")
text_input.bind("<FocusOut>", restore_input_placeholder, add="+")
show_input_placeholder()

btn = ctk.CTkButton(main_frame, text=tr("detect"), height=44,
                    font=ctk.CTkFont("Segoe UI", 14, "bold"), command=detect_voivodeship)
btn.grid(row=2, column=0, padx=22, pady=(0, 18), sticky="ew")

result_label = ctk.CTkLabel(main_frame, text=tr("result"))
result_label.grid(row=3, column=0, padx=22, pady=(0, 8), sticky="w")
output_entry = ctk.CTkTextbox(main_frame, height=110, font=FONT_OUTPUT, state='disabled')
output_entry.grid(row=4, column=0, padx=22, pady=(0, 22), sticky="ew")

btn_frame = ctk.CTkFrame(root, fg_color="transparent")
btn_frame.grid(row=3, column=0, padx=30, pady=(0, 24), sticky="ew")
footer_left = ctk.CTkFrame(btn_frame, fg_color="transparent")
footer_left.pack(side="left")
top_btn = ctk.CTkButton(
    footer_left, text=f"{tr('pin')}: OFF", width=110, height=29,
    fg_color="transparent", border_width=1, command=toggle_topmost,
)
top_btn.pack(pady=(0, 5))
support_button = ctk.CTkButton(
    footer_left, text=tr("support"), width=110, height=29,
    fg_color="transparent", border_width=1, command=open_support,
)
support_button.pack()
about_button = ctk.CTkButton(
    btn_frame, text=tr("about"), width=110, height=29,
    fg_color="transparent", border_width=1, command=show_about,
)
about_button.pack(side="right", anchor="s", pady=(34, 0))

language_selector = ctk.CTkSegmentedButton(
    root,
    values=["PL", "EN"],
    width=76,
    height=28,
    corner_radius=8,
    border_width=1,
    font=ctk.CTkFont("Segoe UI", 10, "bold"),
    command=change_language,
)
language_selector.place(relx=1.0, x=-30, y=38, anchor="ne")
language_selector.set("PL")

root.mainloop()
