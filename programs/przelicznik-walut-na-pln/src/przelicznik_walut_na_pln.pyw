import tkinter as tk
import customtkinter as ctk
import requests
import ast
import datetime
import os
import re
import sys
import threading
import webbrowser
from app_common import apply_window_icon, styled_messagebox as messagebox

ctk.set_appearance_mode("dark")

# Spójna paleta w stylu premium: głęboki granat, grafit i ciepłe złoto.
COLOR_WINDOW = "#0B1120"
COLOR_CARD = "#151E2E"
COLOR_CARD_HOVER = "#1C2940"
COLOR_INPUT = "#0F1726"
COLOR_BORDER = "#34445E"
COLOR_ACCENT = "#C79A3B"
COLOR_ACCENT_HOVER = "#D8AD50"
COLOR_ACCENT_TEXT = "#111827"
COLOR_TEXT = "#F4F1E8"
COLOR_MUTED = "#98A6BA"

APP_TITLE = "Przelicznik walut → PLN"
APP_VERSION = "4.7.0"
APP_AUTHOR = "Beniamin Żak"
APP_DESCRIPTION = (
    "Przelicza EUR, USD, GBP, CHF, CNY i CZK na PLN według średnich "
    "kursów NBP i zawiera podręczny kalkulator."
)

SUPPORT_URLS = {
    "pl": "https://buycoffee.to/beniamin-tv6",
    "en": "https://ko-fi.com/beniaminzak",
}

TRANSLATIONS = {
    "pl": {
        "window_title": "Przelicznik walut → PLN",
        "title": "Przelicznik walut → PLN",
        "subtitle": "Aktualne średnie kursy Narodowego Banku Polskiego",
        "description": "Przelicza EUR, USD, GBP, CHF, CNY i CZK na PLN według średnich kursów NBP i zawiera podręczny kalkulator.",
        "no_data": "brak danych",
        "loading": "pobieranie...",
        "fresh_data": "Najświeższe dane z NBP",
        "older_data": "Dane NBP z {date}. Kolejna aktualizacja w najbliższy dzień roboczy.",
        "future_data": "Data danych NBP jest późniejsza niż data systemowa",
        "fallback_data": "Brak aktualnych danych z NBP — użyto kursu awaryjnego",
        "error": "Błąd",
        "invalid_pln": "Wprowadź poprawną kwotę w zł.",
        "invalid_currency": "Wprowadź poprawną kwotę w {symbol}.",
        "history_empty": "Brak zapisanych wyników",
        "history_copied": "Skopiowano wynik historyczny",
        "division_zero": "Nie można dzielić przez zero",
        "incomplete": "Niepełne działanie",
        "final_copied": "Skopiowano finalny wynik",
        "about": "O mnie",
        "about_title": "O mnie",
        "name": "Nazwa",
        "version": "Wersja",
        "author": "Autor",
        "rate": "Aktualny kurs: {rate} PLN za 1 {code}",
        "update": "Aktualizacja: {date}",
        "amount_pln": "Kwota w zł",
        "amount_foreign": "Kwota w {symbol}",
        "convert_to": "Przelicz na {symbol}",
        "convert_pln": "Przelicz na zł",
        "fetch_error": "Nie udało się pobrać aktualnego kursu {code}: {error}.\nUżyto kursu awaryjnego: {rate} PLN za 1 {code}",
        "show_calculator": "Wysuń kalkulator",
        "hide_calculator": "Wsuń kalkulator",
        "loading_rate": "Pobieranie aktualnego kursu...",
        "amount_tooltip": "Kwota automatycznie zaokrąglona do 2 miejsc po przecinku",
        "copy": "Kopiuj",
        "calculator": "Kalkulator",
        "history": "Historia wyników",
        "copy_currency": "Kopiuj wynik z walutą",
        "pin": "Przypnij",
        "support": "Wsparcie  ♥",
    },
    "en": {
        "window_title": "Currency Converter → PLN",
        "title": "Currency Converter → PLN",
        "subtitle": "Current average exchange rates from the National Bank of Poland",
        "description": "Converts EUR, USD, GBP, CHF, CNY, and CZK to PLN using average NBP rates and includes a handy calculator.",
        "no_data": "no data",
        "loading": "loading...",
        "fresh_data": "Latest data from NBP",
        "older_data": "NBP data from {date}. The next update is expected on the next business day.",
        "future_data": "The NBP data date is later than the system date",
        "fallback_data": "Current NBP data unavailable — a fallback rate is being used",
        "error": "Error",
        "invalid_pln": "Enter a valid amount in PLN.",
        "invalid_currency": "Enter a valid amount in {symbol}.",
        "history_empty": "No saved results",
        "history_copied": "Historical result copied",
        "division_zero": "Cannot divide by zero",
        "incomplete": "Incomplete calculation",
        "final_copied": "Final result copied",
        "about": "About",
        "about_title": "About",
        "name": "Name",
        "version": "Version",
        "author": "Author",
        "rate": "Current rate: {rate} PLN for 1 {code}",
        "update": "Updated: {date}",
        "amount_pln": "Amount in PLN",
        "amount_foreign": "Amount in {symbol}",
        "convert_to": "Convert to {symbol}",
        "convert_pln": "Convert to PLN",
        "fetch_error": "Could not download the current {code} rate: {error}.\nFallback rate used: {rate} PLN for 1 {code}",
        "show_calculator": "Show calculator",
        "hide_calculator": "Hide calculator",
        "loading_rate": "Downloading the current rate...",
        "amount_tooltip": "The amount is automatically rounded to 2 decimal places",
        "copy": "Copy",
        "calculator": "Calculator",
        "history": "Result history",
        "copy_currency": "Copy result with currency",
        "pin": "Pin",
        "support": "Support  ♥",
    },
}

CURRENCY_NAMES = {
    "pl": {
        "EUR": "Euro", "USD": "Dolar amerykański", "GBP": "Funt brytyjski",
        "CHF": "Frank szwajcarski", "CNY": "Juan chiński", "CZK": "Korona czeska",
    },
    "en": {
        "EUR": "Euro", "USD": "US dollar", "GBP": "British pound",
        "CHF": "Swiss franc", "CNY": "Chinese yuan", "CZK": "Czech koruna",
    },
}

current_language = "pl"


def tr(key, **values):
    text = TRANSLATIONS[current_language][key]
    return text.format(**values) if values else text


def localized_number(value, digits=2):
    text = f"{value:.{digits}f}"
    return text.replace(".", ",") if current_language == "pl" else text

WALUTY = {
    "EUR": {"nazwa": "Euro", "symbol": "€", "kurs_awaryjny": 4.50},
    "USD": {"nazwa": "Dolar amerykański", "symbol": "$", "kurs_awaryjny": 4.00},
    "GBP": {"nazwa": "Funt brytyjski", "symbol": "£", "kurs_awaryjny": 5.20},
    "CHF": {"nazwa": "Frank szwajcarski", "symbol": "CHF", "kurs_awaryjny": 4.75},
    "CNY": {"nazwa": "Juan chiński", "symbol": "¥", "kurs_awaryjny": 0.55},
    "CZK": {"nazwa": "Korona czeska", "symbol": "Kč", "kurs_awaryjny": 0.18},
}
symbol_waluty = {kod: dane["symbol"] for kod, dane in WALUTY.items()}

calculator_expression = ""
calculator_just_evaluated = False
calculator_currency = ""
calculator_history = []
calculator_history_open = False
calculator_history_animating = False
calculator_notice_job = None

CALCULATOR_PANEL_Y = 222
CALCULATOR_PANEL_HEIGHT = 455
CALCULATOR_CONTENT_Y = 42
HISTORY_EXPANSION = 146


# Funkcja do pobierania najbardziej aktualnego średniego kursu waluty wraz z datą aktualizacji
def pobierz_sredni_kurs(waluta):
    try:
        url = f"https://api.nbp.pl/api/exchangerates/rates/a/{waluta}/last/1/"
        response = requests.get(url, headers={"User-Agent": "Currency-Converter-Client"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        kurs = data['rates'][0]['mid']
        effective_date = data['rates'][0]['effectiveDate']
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        data_aktualizacji = effective_date + " " + current_time
        return kurs, data_aktualizacji, None
    except Exception as e:
        return WALUTY[waluta]["kurs_awaryjny"], tr("no_data"), str(e)


def tekst_statusu_danych(data_kursu_z_czasem, dzis=None):
    """Zwraca krótką informację o aktualności tabeli kursów NBP."""
    try:
        data_kursu = datetime.date.fromisoformat(data_kursu_z_czasem.split()[0])
        dzis = dzis or datetime.date.today()
        if data_kursu == dzis:
            return tr("fresh_data")
        if data_kursu < dzis:
            return tr("older_data", date=data_kursu.strftime('%d.%m.%Y'))
        return tr("future_data")
    except (ValueError, IndexError):
        return tr("fallback_data")

# Przeliczanie walut
def przelicz_na_walute(event=None):
    global aktualny_kurs, aktualna_waluta
    try:
        pln = float(entry_pln.get().replace(",", "."))
        wynik = pln / aktualny_kurs
        label_waluta_result.configure(
            text=localized_number(wynik) + f" {symbol_waluty[aktualna_waluta]}"
        )
    except ValueError:
        messagebox.showerror(tr("error"), tr("invalid_pln"))

def przelicz_na_pln(event=None):
    global aktualny_kurs, aktualna_waluta
    try:
        kwota = float(entry_waluta.get().replace(",", "."))
        wynik = kwota * aktualny_kurs
        label_pln_result.configure(
            text=localized_number(wynik) + (" zł" if current_language == "pl" else " PLN")
        )
    except ValueError:
        messagebox.showerror(
            tr("error"), tr("invalid_currency", symbol=symbol_waluty[aktualna_waluta])
        )

def skopiuj_wynik(label):
    wynik = label.cget("text").strip()
    if wynik and wynik != "—":
        if wynik.endswith((" zł", " PLN")):
            numeric_value = wynik.rsplit(" ", 1)[0].strip()
            root.clipboard_clear()
            root.clipboard_append(numeric_value)
        else:
            root.clipboard_clear()
            root.clipboard_append(wynik)
        ustaw_kalkulator_z_tekstu(wynik)


def oblicz_wyrazenie(expression):
    """Bezpiecznie oblicza podstawowe działanie bez używania eval()."""
    operators = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.USub: lambda value: -value,
        ast.UAdd: lambda value: value,
    }

    def calculate(node):
        if isinstance(node, ast.Expression):
            return calculate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            return operators[type(node.op)](calculate(node.left), calculate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
            return operators[type(node.op)](calculate(node.operand))
        raise ValueError("Niedozwolone działanie")

    if not expression or len(expression) > 80:
        raise ValueError("Niepełne działanie")
    return calculate(ast.parse(expression, mode="eval"))


def formatuj_liczbe_kalkulatora(value):
    if abs(value) < 1e-12:
        value = 0
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.10f}".rstrip("0").rstrip(".")


def odswiez_wyswietlacz_kalkulatora(text=None):
    if text is None:
        text = calculator_expression or "0"
        text = text.replace("*", " × ").replace("/", " ÷ ").replace("+", " + ")
        text = text.replace("-", " − ")
        if current_language == "pl":
            text = text.replace(".", ",")
        text = " ".join(text.split())
        if len(text) > 24:
            text = "…" + text[-23:]
    calculator_display.configure(text=text)


def symbol_waluty_z_tekstu(text):
    for symbol in ("zł", "PLN", *sorted(set(symbol_waluty.values()), key=len, reverse=True)):
        if symbol in text:
            return symbol
    return ""


def formatuj_wynik_z_waluta(value, currency=""):
    number = formatuj_liczbe_kalkulatora(float(value))
    if current_language == "pl":
        number = number.replace(".", ",")
    return f"{number} {currency}".strip()


def odswiez_historie_kalkulatora():
    for widget in calculator_history_frame.winfo_children():
        widget.destroy()

    if not calculator_history:
        ctk.CTkLabel(
            calculator_history_frame,
            text=tr("history_empty"),
            text_color=COLOR_MUTED,
        ).pack(pady=18)
        return

    for result in reversed(calculator_history):
        ctk.CTkButton(
            calculator_history_frame,
            text=result,
            height=34,
            anchor="e",
            fg_color=COLOR_INPUT,
            hover_color=COLOR_CARD_HOVER,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
            command=lambda selected=result: skopiuj_wynik_historyczny(selected),
        ).pack(fill="x", padx=2, pady=3)


def dodaj_do_historii_kalkulatora(value, currency=None):
    currency = calculator_currency if currency is None else currency
    result = formatuj_wynik_z_waluta(value, currency)
    if not calculator_history or calculator_history[-1] != result:
        calculator_history.append(result)
        del calculator_history[:-100]
    odswiez_historie_kalkulatora()


def pokaz_monit_kalkulatora(text):
    global calculator_notice_job
    calculator_notice.configure(text=text)
    calculator_notice.place(x=16, y=371)
    calculator_notice.lift()
    if calculator_notice_job is not None:
        root.after_cancel(calculator_notice_job)
    calculator_notice_job = root.after(2400, calculator_notice.place_forget)


def skopiuj_wynik_historyczny(result):
    root.clipboard_clear()
    root.clipboard_append(result)
    toggle_historii_kalkulatora(force_close=True)
    pokaz_monit_kalkulatora(tr("history_copied"))


def animuj_historie_kalkulatora(opening, step=0, steps=16):
    global calculator_history_animating
    progress = step / steps
    eased = progress * progress * (3 - 2 * progress)
    delta = round(HISTORY_EXPANSION * (eased if opening else 1 - eased))

    calculator_panel.configure(height=CALCULATOR_PANEL_HEIGHT + delta)
    calculator_panel.place_configure(y=CALCULATOR_PANEL_Y - delta)
    calculator_content.place_configure(y=CALCULATOR_CONTENT_Y + delta)

    if step < steps:
        root.after(
            12,
            lambda: animuj_historie_kalkulatora(opening, step + 1, steps),
        )
        return

    calculator_history_animating = False
    if opening:
        calculator_history_info.place(x=124, y=17)
        calculator_history_info.lift()
    else:
        calculator_history_frame.place_forget()


def toggle_historii_kalkulatora(event=None, force_close=False):
    global calculator_history_open, calculator_history_animating
    if calculator_history_animating:
        return
    if force_close and not calculator_history_open:
        return

    opening = not calculator_history_open and not force_close
    calculator_history_open = opening
    calculator_history_animating = True
    if opening:
        odswiez_historie_kalkulatora()
        calculator_history_frame.place(x=16, y=48)
        calculator_history_frame.lift()
        calculator_content.lift()
        calculator_title.lift()
    else:
        calculator_history_info.place_forget()
        calculator_content.lift()
        calculator_title.lift()
    animuj_historie_kalkulatora(opening)


def widget_wewnatrz(widget, container):
    while widget is not None:
        if widget == container:
            return True
        widget = getattr(widget, "master", None)
    return False


def zamknij_historie_po_kliknieciu_tla(event):
    if not calculator_history_open or calculator_history_animating:
        return
    if widget_wewnatrz(event.widget, calculator_history_frame):
        return
    if widget_wewnatrz(event.widget, calculator_display):
        return
    toggle_historii_kalkulatora(force_close=True)


def ostatni_fragment_liczbowy(expression):
    last_operator = max((expression.rfind(operator) for operator in "+-*/"), default=-1)
    return expression[last_operator + 1:]


def nacisnij_kalkulator(value):
    global calculator_expression, calculator_just_evaluated, calculator_currency

    if value == "C":
        calculator_expression = ""
        calculator_just_evaluated = False
        calculator_currency = ""
    elif value == "back":
        calculator_expression = calculator_expression[:-1]
        calculator_just_evaluated = False
    elif value == "negate":
        try:
            calculator_expression = formatuj_liczbe_kalkulatora(
                -float(oblicz_wyrazenie(calculator_expression))
            )
            calculator_just_evaluated = True
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError):
            return
    elif value == "=":
        try:
            calculator_expression = formatuj_liczbe_kalkulatora(
                float(oblicz_wyrazenie(calculator_expression))
            )
            calculator_just_evaluated = True
            dodaj_do_historii_kalkulatora(calculator_expression)
        except ZeroDivisionError:
            calculator_expression = ""
            calculator_just_evaluated = False
            odswiez_wyswietlacz_kalkulatora(tr("division_zero"))
            return
        except (ValueError, SyntaxError, TypeError):
            odswiez_wyswietlacz_kalkulatora(tr("incomplete"))
            return
    elif value in "+-*/":
        if calculator_expression and calculator_expression[-1] in "+-*/":
            calculator_expression = calculator_expression[:-1] + value
        elif calculator_expression:
            calculator_expression += value
        elif value == "-":
            calculator_expression = "-"
        calculator_just_evaluated = False
    elif value == ".":
        if calculator_just_evaluated:
            calculator_expression = "0"
        if "." not in ostatni_fragment_liczbowy(calculator_expression):
            if not calculator_expression or calculator_expression[-1] in "+-*/":
                calculator_expression += "0"
            calculator_expression += "."
        calculator_just_evaluated = False
    else:
        if calculator_just_evaluated:
            calculator_expression = ""
        calculator_expression += value
        calculator_just_evaluated = False

    odswiez_wyswietlacz_kalkulatora()


def ustaw_kalkulator_z_tekstu(text):
    global calculator_expression, calculator_just_evaluated, calculator_currency
    cleaned = "".join(character for character in text if character.isdigit() or character in ",.-")
    cleaned = cleaned.replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        return False
    formatted_value = formatuj_liczbe_kalkulatora(value)
    incoming_currency = symbol_waluty_z_tekstu(text)
    if calculator_expression and calculator_expression[-1] in "+-*/":
        calculator_expression += formatted_value
        calculator_just_evaluated = False
    else:
        calculator_expression = formatted_value
        calculator_just_evaluated = True
        calculator_currency = incoming_currency
    if incoming_currency and not calculator_currency:
        calculator_currency = incoming_currency
    dodaj_do_historii_kalkulatora(formatted_value, incoming_currency)
    odswiez_wyswietlacz_kalkulatora()
    return True


def kopiuj_z_kalkulatora():
    global calculator_expression, calculator_just_evaluated, calculator_currency
    if calculator_expression:
        try:
            result = formatuj_liczbe_kalkulatora(
                float(oblicz_wyrazenie(calculator_expression))
            )
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError):
            odswiez_wyswietlacz_kalkulatora(tr("incomplete"))
            return
        calculator_expression = result
        calculator_just_evaluated = True
        dodaj_do_historii_kalkulatora(result)
        odswiez_wyswietlacz_kalkulatora()
        if not calculator_currency:
            calculator_currency = symbol_waluty[aktualna_waluta]
        copied_result = formatuj_wynik_z_waluta(result, calculator_currency)
        root.clipboard_clear()
        root.clipboard_append(copied_result)
        pokaz_monit_kalkulatora(tr("final_copied"))


def obsluz_klawiature_kalkulatora(event):
    if not calculator_open:
        return None
    focused_widget = root.focus_get()
    if isinstance(focused_widget, (tk.Entry, tk.Text)):
        return None

    key_map = {
        "Return": "=", "KP_Enter": "=", "BackSpace": "back", "Escape": "C",
        "KP_Add": "+", "KP_Subtract": "-", "KP_Multiply": "*",
        "KP_Divide": "/", "KP_Decimal": ".", "Delete": "C",
    }
    value = key_map.get(event.keysym)
    if value is None and event.char in "0123456789+-*/":
        value = event.char
    elif value is None and event.char in ",.":
        value = "."
    if value is None:
        return None
    if calculator_history_open:
        toggle_historii_kalkulatora(force_close=True)
    nacisnij_kalkulator(value)
    return "break"

# Informacje
def pokaz_informacje_o_autorze():
    messagebox.showinfo(
        tr("about_title"),
        f"{tr('name')}: {tr('window_title')}\n{tr('version')}: {APP_VERSION}\n"
        f"{tr('author')}: {APP_AUTHOR}\n\n{tr('description')}",
    )


def open_support():
    webbrowser.open(SUPPORT_URLS[current_language])

# Ustawienie waluty i kursu
SPINNER_FRAMES = ("◐", "◓", "◑", "◒")
loading_active = False
spinner_frame_index = 0


def animuj_ladowanie():
    global spinner_frame_index
    if not loading_active:
        return
    loading_label.configure(text=SPINNER_FRAMES[spinner_frame_index])
    spinner_frame_index = (spinner_frame_index + 1) % len(SPINNER_FRAMES)
    root.after(110, animuj_ladowanie)


def ustaw_wyglad_przyciskow_walut(wybrana_waluta):
    for kod, button in currency_buttons.items():
        aktywny = kod == wybrana_waluta
        button.configure(
            fg_color=COLOR_ACCENT if aktywny else COLOR_INPUT,
            hover_color=COLOR_ACCENT_HOVER if aktywny else COLOR_CARD_HOVER,
            text_color=COLOR_ACCENT_TEXT if aktywny else COLOR_TEXT,
        )


def rozpocznij_ladowanie(waluta):
    global loading_active, spinner_frame_index
    loading_active = True
    spinner_frame_index = 0
    ustaw_wyglad_przyciskow_walut(waluta)
    for button in currency_buttons.values():
        button.configure(state="disabled")
    loading_label.place(relx=0.95, rely=0.72, anchor="center")
    animuj_ladowanie()


def zakoncz_ladowanie():
    global loading_active
    loading_active = False
    loading_label.place_forget()
    for button in currency_buttons.values():
        button.configure(state="normal")


def zastosuj_nowy_kurs(waluta, kurs, data, blad):
    global aktualna_waluta, aktualny_kurs, data_aktualizacji
    aktualna_waluta = waluta
    aktualny_kurs = kurs
    data_aktualizacji = data
    label_header.configure(
        text=tr("rate", rate=localized_number(aktualny_kurs, 4), code=waluta)
    )
    label_update.configure(text=tr("update", date=data_aktualizacji))
    label_pln.configure(text=tr("amount_pln"))
    label_waluta.configure(text=tr("amount_foreign", symbol=symbol_waluty[waluta]))
    button_pln.configure(text=tr("convert_to", symbol=symbol_waluty[waluta]))
    button_waluta.configure(text=tr("convert_pln"))
    entry_pln.configure(placeholder_text="0,00" if current_language == "pl" else "0.00")
    entry_waluta.configure(placeholder_text="0,00" if current_language == "pl" else "0.00")
    label_waluta_result.configure(text="—")
    label_pln_result.configure(text="—")
    entry_pln.delete(0, tk.END)
    entry_waluta.delete(0, tk.END)
    zakoncz_ladowanie()
    if blad:
        messagebox.showwarning(
            tr("error"),
            tr(
                "fetch_error",
                code=waluta,
                error=blad,
                rate=localized_number(kurs, 4),
            ),
        )

def ustaw_walute(waluta):
    if waluta not in WALUTY or loading_active:
        return
    rozpocznij_ladowanie(waluta)

    def pobierz_w_tle():
        wynik = pobierz_sredni_kurs(waluta)
        root.after(0, lambda: zastosuj_nowy_kurs(waluta, *wynik))

    threading.Thread(target=pobierz_w_tle, daemon=True).start()

# --- GUI ---
root = ctk.CTk()
root.title(tr("window_title"))
root.geometry("620x776")
root.resizable(False, False)
root.configure(fg_color=COLOR_WINDOW)
apply_window_icon(root)

main_content = ctk.CTkFrame(root, width=620, height=776, fg_color="transparent")
main_content.place(x=0, y=0)
main_content.pack_propagate(False)

# Flaga always-on-top
is_topmost = False

def toggle_topmost():
    global is_topmost
    is_topmost = not is_topmost
    root.attributes('-topmost', is_topmost)
    top_btn.configure(
        text=f"{tr('pin')}: {'ON' if is_topmost else 'OFF'}",
        fg_color=COLOR_ACCENT if is_topmost else COLOR_INPUT,
        hover_color=COLOR_ACCENT_HOVER if is_topmost else COLOR_CARD_HOVER,
        text_color=COLOR_ACCENT_TEXT if is_topmost else COLOR_TEXT,
    )


COLLAPSED_WIDTH = 620
EXPANDED_WIDTH = 920
WINDOW_HEIGHT = 776
ABOUT_COLLAPSED_X = 496
ABOUT_Y = 735
calculator_open = False
calculator_animating = False
calculator_collapsed_position = None


def pokaz_strzalke_przelacznika(event=None):
    if not calculator_open and not calculator_animating:
        calculator_toggle_arrow.configure(text="→")
        calculator_toggle_arrow.place(x=596, y=72)


def ukryj_strzalke_przelacznika(event=None):
    if not calculator_open:
        calculator_toggle_arrow.place_forget()


def animuj_szerokosc_okna(start_width, end_width, start_x, end_x, step=0, steps=18):
    global calculator_animating, calculator_open
    progress = step / steps
    eased = progress * progress * (3 - 2 * progress)
    width = round(start_width + (end_width - start_width) * eased)
    x = round(start_x + (end_x - start_x) * eased)
    root.geometry(f"{width}x{WINDOW_HEIGHT}+{x}+{root.winfo_y()}")
    about_btn.place_configure(x=ABOUT_COLLAPSED_X + width - COLLAPSED_WIDTH)

    if step < steps:
        root.after(
            12,
            lambda: animuj_szerokosc_okna(
                start_width, end_width, start_x, end_x, step + 1, steps
            ),
        )
        return

    calculator_animating = False
    calculator_open = end_width == EXPANDED_WIDTH
    calculator_toggle_btn.configure(
        text=tr("hide_calculator") if calculator_open else tr("show_calculator")
    )
    if calculator_open:
        calculator_toggle_arrow.configure(text="←")
        calculator_toggle_arrow.place(x=596, y=72)
        copy_arrow_pln.grid()
        copy_arrow_waluta.grid()
        root.focus_set()
    else:
        calculator_toggle_arrow.place_forget()
        copy_arrow_pln.grid_remove()
        copy_arrow_waluta.grid_remove()
        toggle_historii_kalkulatora(force_close=True)


def toggle_calculator():
    global calculator_animating, calculator_collapsed_position
    if calculator_animating:
        return

    root.update_idletasks()
    calculator_animating = True
    calculator_toggle_arrow.place_forget()
    current_x = root.winfo_x()
    current_width = root.winfo_width()

    if calculator_open:
        copy_arrow_pln.grid_remove()
        copy_arrow_waluta.grid_remove()
        toggle_historii_kalkulatora(force_close=True)
        target_x = calculator_collapsed_position[0] if calculator_collapsed_position else current_x
        animuj_szerokosc_okna(current_width, COLLAPSED_WIDTH, current_x, target_x)
    else:
        calculator_collapsed_position = (current_x, root.winfo_y())
        screen_width = root.winfo_screenwidth()
        target_x = min(current_x, max(10, screen_width - EXPANDED_WIDTH - 10))
        calculator_panel.lift()
        animuj_szerokosc_okna(current_width, EXPANDED_WIDTH, current_x, target_x)

# Ustawienia początkowe waluty
aktualna_waluta = "EUR"
aktualny_kurs = 0.0
data_aktualizacji = tr("loading")

main_title_label = ctk.CTkLabel(
    main_content, text=tr("title"), text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 28, "bold"),
)
main_title_label.pack(anchor="w", padx=30, pady=(26, 8))
subtitle_label = ctk.CTkLabel(main_content, text=tr("subtitle"), text_color=COLOR_MUTED)
subtitle_label.pack(anchor="w", padx=30, pady=(0, 16))

calculator_toggle_btn = ctk.CTkButton(
    main_content,
    text=tr("show_calculator"),
    width=132,
    height=28,
    fg_color=COLOR_INPUT,
    hover_color=COLOR_CARD_HOVER,
    border_color=COLOR_BORDER,
    border_width=1,
    text_color=COLOR_TEXT,
    command=toggle_calculator,
)
calculator_toggle_btn.place(x=590, y=72, anchor="ne")
calculator_toggle_btn.bind("<Enter>", pokaz_strzalke_przelacznika)
calculator_toggle_btn.bind("<Leave>", ukryj_strzalke_przelacznika)

calculator_toggle_arrow = ctk.CTkLabel(
    main_content,
    text="",
    width=20,
    height=28,
    text_color=COLOR_ACCENT,
    font=ctk.CTkFont("Segoe UI", 21, "bold"),
)

currency_selector = ctk.CTkFrame(main_content, fg_color="transparent")
currency_selector.pack(fill="x", padx=30, pady=(0, 16))
for column in (0, 1):
    currency_selector.grid_columnconfigure(column, weight=1, uniform="currency")

currency_buttons = {}
uklad_walut = (
    ("EUR", "USD"),
    ("GBP", "CHF"),
    ("CNY", "CZK"),
)
for row, codes in enumerate(uklad_walut):
    for column, kod in enumerate(codes):
        dane = WALUTY[kod]
        button = ctk.CTkButton(
            currency_selector,
            text=f"{kod} · {CURRENCY_NAMES[current_language][kod]}",
            height=28,
            corner_radius=6,
            fg_color=COLOR_INPUT,
            hover_color=COLOR_CARD_HOVER,
            border_width=0,
            text_color=COLOR_TEXT,
            command=lambda wybrany=kod: ustaw_walute(wybrany),
        )
        button.grid(
            row=row,
            column=column,
            padx=(0, 3) if column == 0 else (3, 0),
            pady=(0, 3) if row < len(uklad_walut) - 1 else 0,
            sticky="ew",
        )
        currency_buttons[kod] = button

ustaw_wyglad_przyciskow_walut("EUR")

rate_card = ctk.CTkFrame(main_content, corner_radius=18, fg_color=COLOR_CARD)
rate_card.pack(fill="x", padx=30, pady=(0, 16))
label_header = ctk.CTkLabel(
    rate_card,
    text=tr("loading_rate"),
    text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 18, "bold"))
label_header.pack(pady=(18, 4))
label_update = ctk.CTkLabel(rate_card, text=tr("update", date=data_aktualizacji), text_color=COLOR_MUTED)
label_update.pack(pady=(0, 18))
loading_label = ctk.CTkLabel(
    rate_card,
    text="",
    width=28,
    height=28,
    text_color=COLOR_ACCENT,
    font=ctk.CTkFont("Segoe UI Symbol", 24, "bold"),
)

update_tooltip = None
amount_tooltip = None


def pokaz_dymek_aktualizacji(event=None):
    global update_tooltip
    if update_tooltip is not None:
        return

    root.update_idletasks()
    update_tooltip = ctk.CTkLabel(
        main_content,
        text=tekst_statusu_danych(data_aktualizacji),
        fg_color="transparent",
        text_color=COLOR_MUTED,
        height=18,
        font=ctk.CTkFont("Segoe UI", 10),
    )
    gap_center_y = (
        rate_card.winfo_y() + rate_card.winfo_height() + frame_pln.winfo_y()
    ) // 2
    update_tooltip.place(relx=0.5, y=gap_center_y, anchor="center")


def ukryj_dymek_aktualizacji(event=None):
    global update_tooltip
    if update_tooltip is not None:
        update_tooltip.destroy()
        update_tooltip = None


def pokaz_dymek_kwoty(label):
    global amount_tooltip
    if label.cget("text").strip() == "—" or amount_tooltip is not None:
        return
    amount_tooltip = tk.Toplevel(root)
    amount_tooltip.wm_overrideredirect(True)
    amount_tooltip.attributes("-topmost", True)
    tooltip_label = tk.Label(
        amount_tooltip,
        text=tr("amount_tooltip"),
        bg=COLOR_INPUT,
        fg=COLOR_TEXT,
        relief="solid",
        borderwidth=1,
        font=("Segoe UI", 10),
        padx=10,
        pady=6,
    )
    tooltip_label.pack()
    x = label.winfo_rootx()
    y = label.winfo_rooty() + label.winfo_height() + 7
    amount_tooltip.wm_geometry(f"+{x}+{y}")


def ukryj_dymek_kwoty(event=None):
    global amount_tooltip
    if amount_tooltip is not None:
        amount_tooltip.destroy()
        amount_tooltip = None


label_update.bind("<Enter>", pokaz_dymek_aktualizacji)
label_update.bind("<Leave>", ukryj_dymek_aktualizacji)

frame_pln = ctk.CTkFrame(main_content, corner_radius=18, fg_color=COLOR_CARD)
frame_pln.pack(fill="x", padx=30, pady=8)
frame_pln.grid_columnconfigure(0, weight=1)
label_pln = ctk.CTkLabel(
    frame_pln, text=tr("amount_pln"), font=ctk.CTkFont("Segoe UI", 15, "bold"),
)
label_pln.grid(row=0, column=0, columnspan=2, padx=20, pady=(16, 6), sticky="w")
entry_pln = ctk.CTkEntry(
    frame_pln, height=40, placeholder_text="0,00", fg_color=COLOR_INPUT,
    border_color=COLOR_BORDER, text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 17),
)
entry_pln.grid(row=1, column=0, padx=(20, 8), pady=6, sticky="ew")
entry_pln.bind("<Return>", przelicz_na_walute)
button_pln = ctk.CTkButton(frame_pln, text=tr("convert_to", symbol=symbol_waluty[aktualna_waluta]),
                           height=40, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                           text_color=COLOR_ACCENT_TEXT, command=przelicz_na_walute)
button_pln.grid(row=1, column=1, padx=(0, 20), pady=6)
label_waluta_result = ctk.CTkLabel(frame_pln, text="—", font=ctk.CTkFont("Segoe UI", 22, "bold"))
label_waluta_result.grid(row=2, column=0, padx=20, pady=(10, 18), sticky="w")
label_waluta_result.bind("<Enter>", lambda event: pokaz_dymek_kwoty(label_waluta_result))
label_waluta_result.bind("<Leave>", ukryj_dymek_kwoty)
copy_button_pln = ctk.CTkButton(
    frame_pln, text=tr("copy"), width=90, fg_color=COLOR_INPUT,
    hover_color=COLOR_CARD_HOVER, border_color=COLOR_BORDER, border_width=1,
    command=lambda: skopiuj_wynik(label_waluta_result),
)
copy_button_pln.grid(row=2, column=1, padx=(0, 5), pady=(10, 18))
copy_arrow_pln = ctk.CTkLabel(
    frame_pln, text="→", width=18, text_color=COLOR_ACCENT,
    font=ctk.CTkFont("Segoe UI", 21, "bold"),
)
copy_arrow_pln.grid(row=2, column=2, padx=(0, 14), pady=(10, 18))
copy_arrow_pln.grid_remove()

frame_waluta = ctk.CTkFrame(main_content, corner_radius=18, fg_color=COLOR_CARD)
frame_waluta.pack(fill="x", padx=30, pady=8)
frame_waluta.grid_columnconfigure(0, weight=1)
label_waluta = ctk.CTkLabel(
    frame_waluta,
    text=tr("amount_foreign", symbol=symbol_waluty[aktualna_waluta]),
    font=ctk.CTkFont("Segoe UI", 15, "bold"),
)
label_waluta.grid(row=0, column=0, columnspan=2, padx=20, pady=(16, 6), sticky="w")
entry_waluta = ctk.CTkEntry(
    frame_waluta, height=40, placeholder_text="0,00", fg_color=COLOR_INPUT,
    border_color=COLOR_BORDER, text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 17),
)
entry_waluta.grid(row=1, column=0, padx=(20, 8), pady=6, sticky="ew")
entry_waluta.bind("<Return>", przelicz_na_pln)
button_waluta = ctk.CTkButton(
    frame_waluta, text=tr("convert_pln"), height=40, fg_color=COLOR_ACCENT,
    hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_ACCENT_TEXT, command=przelicz_na_pln,
)
button_waluta.grid(row=1, column=1, padx=(0, 20), pady=6)
label_pln_result = ctk.CTkLabel(frame_waluta, text="—", font=ctk.CTkFont("Segoe UI", 22, "bold"))
label_pln_result.grid(row=2, column=0, padx=20, pady=(10, 18), sticky="w")
label_pln_result.bind("<Enter>", lambda event: pokaz_dymek_kwoty(label_pln_result))
label_pln_result.bind("<Leave>", ukryj_dymek_kwoty)
copy_button_waluta = ctk.CTkButton(
    frame_waluta, text=tr("copy"), width=90, fg_color=COLOR_INPUT,
    hover_color=COLOR_CARD_HOVER, border_color=COLOR_BORDER, border_width=1,
    command=lambda: skopiuj_wynik(label_pln_result),
)
copy_button_waluta.grid(row=2, column=1, padx=(0, 5), pady=(10, 18))
copy_arrow_waluta = ctk.CTkLabel(
    frame_waluta, text="→", width=18, text_color=COLOR_ACCENT,
    font=ctk.CTkFont("Segoe UI", 21, "bold"),
)
copy_arrow_waluta.grid(row=2, column=2, padx=(0, 14), pady=(10, 18))
copy_arrow_waluta.grid_remove()

# Panel kalkulatora znajduje się poza podstawowym obszarem okna. Zostaje
# odsłonięty dopiero podczas animowanego poszerzania aplikacji.
calculator_panel = ctk.CTkFrame(
    root,
    width=270,
    height=CALCULATOR_PANEL_HEIGHT,
    corner_radius=18,
    fg_color=COLOR_CARD,
)
calculator_panel.place(x=632, y=CALCULATOR_PANEL_Y)
calculator_panel.pack_propagate(False)

calculator_content = ctk.CTkFrame(
    calculator_panel,
    width=270,
    height=CALCULATOR_PANEL_HEIGHT - CALCULATOR_CONTENT_Y,
    fg_color="transparent",
)
calculator_content.place(x=0, y=CALCULATOR_CONTENT_Y)
calculator_content.pack_propagate(False)

calculator_title = ctk.CTkLabel(
    calculator_panel,
    text=tr("calculator"),
    text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 18, "bold"),
)
calculator_title.place(x=16, y=14)
calculator_title.bind(
    "<Button-1>", lambda event: toggle_historii_kalkulatora(force_close=True)
)

calculator_history_info = ctk.CTkLabel(
    calculator_panel,
    text=tr("history"),
    text_color=COLOR_MUTED,
    font=ctk.CTkFont("Segoe UI", 12, "bold"),
)
calculator_history_info.bind(
    "<Button-1>", lambda event: toggle_historii_kalkulatora(force_close=True)
)

calculator_display = ctk.CTkButton(
    calculator_content,
    text="0",
    width=238,
    height=52,
    corner_radius=10,
    fg_color=COLOR_INPUT,
    text_color=COLOR_TEXT,
    hover=False,
    anchor="e",
    font=ctk.CTkFont("Segoe UI", 22, "bold"),
    command=toggle_historii_kalkulatora,
)
calculator_display.pack(padx=16, pady=(0, 10))

calculator_history_frame = ctk.CTkScrollableFrame(
    calculator_panel,
    width=226,
    height=70,
    corner_radius=10,
    fg_color=COLOR_INPUT,
    scrollbar_button_color=COLOR_BORDER,
    scrollbar_button_hover_color=COLOR_ACCENT,
)

calculator_notice = ctk.CTkLabel(
    calculator_content,
    text="",
    width=238,
    height=28,
    corner_radius=8,
    fg_color=COLOR_CARD_HOVER,
    text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 12, "bold"),
)

calculator_keypad = ctk.CTkFrame(calculator_content, fg_color="transparent")
calculator_keypad.pack(fill="x", padx=12)
for column in range(4):
    calculator_keypad.grid_columnconfigure(column, weight=1)

calculator_keys = (
    (("7", "7"), ("8", "8"), ("9", "9"), ("÷", "/")),
    (("4", "4"), ("5", "5"), ("6", "6"), ("×", "*")),
    (("1", "1"), ("2", "2"), ("3", "3"), ("−", "-")),
    (("0", "0"), ("00", "00"), (",", "."), ("+", "+")),
    (("C", "C"), ("±", "negate"), ("⌫", "back"), ("=", "=")),
)

for row, keys in enumerate(calculator_keys):
    for column, (label, value) in enumerate(keys):
        accent = value in ("/", "*", "-", "+", "=")
        ctk.CTkButton(
            calculator_keypad,
            text=label,
            width=52,
            height=43,
            corner_radius=9,
            fg_color=COLOR_ACCENT if accent else COLOR_INPUT,
            hover_color=COLOR_ACCENT_HOVER if accent else COLOR_CARD_HOVER,
            border_color=COLOR_BORDER,
            border_width=0 if accent else 1,
            text_color=COLOR_ACCENT_TEXT if accent else COLOR_TEXT,
            font=ctk.CTkFont("Segoe UI", 15, "bold" if accent else "normal"),
            command=lambda key=value: nacisnij_kalkulator(key),
        ).grid(row=row, column=column, padx=3, pady=3, sticky="ew")

calculator_copy_button = ctk.CTkButton(
    calculator_content,
    text=tr("copy_currency"),
    width=238,
    height=32,
    fg_color=COLOR_INPUT,
    hover_color=COLOR_CARD_HOVER,
    border_color=COLOR_BORDER,
    border_width=1,
    text_color=COLOR_TEXT,
    command=kopiuj_z_kalkulatora,
)
calculator_copy_button.pack(padx=16, pady=(10, 0))

odswiez_wyswietlacz_kalkulatora()
odswiez_historie_kalkulatora()

footer = ctk.CTkFrame(main_content, fg_color="transparent")
footer.pack(side="bottom", fill="x", padx=14, pady=(8, 12))
footer.grid_columnconfigure(1, weight=1)

FOOTER_BUTTON_WIDTH = 110
footer_button_style = {
    "width": FOOTER_BUTTON_WIDTH,
    "height": 29,
    "fg_color": COLOR_INPUT,
    "hover_color": COLOR_CARD_HOVER,
    "border_color": COLOR_BORDER,
    "border_width": 1,
    "text_color": COLOR_TEXT,
}

top_btn = ctk.CTkButton(
    footer, text=f"{tr('pin')}: OFF", command=toggle_topmost, **footer_button_style,
)
top_btn.grid(row=0, column=0, pady=(0, 6), sticky="w")
support_button = ctk.CTkButton(
    footer, text=tr("support"), command=open_support, **footer_button_style,
)
support_button.grid(row=1, column=0, sticky="w")
about_btn = ctk.CTkButton(
    root, text=tr("about"), command=pokaz_informacje_o_autorze, **footer_button_style,
)
about_btn.place(x=ABOUT_COLLAPSED_X, y=ABOUT_Y)


def reformat_result_label(label, suffix):
    text = label.cget("text").strip()
    if not text or text == "—":
        return
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", text)
    if not match:
        return
    value = float(match.group(0).replace(",", "."))
    label.configure(text=f"{localized_number(value)} {suffix}")


def change_language(selected_language):
    global current_language

    current_language = selected_language.lower()
    root.title(tr("window_title"))
    main_title_label.configure(text=tr("title"))
    subtitle_label.configure(text=tr("subtitle"))
    calculator_toggle_btn.configure(
        text=tr("hide_calculator") if calculator_open else tr("show_calculator")
    )
    for code, button in currency_buttons.items():
        button.configure(text=f"{code} · {CURRENCY_NAMES[current_language][code]}")

    if aktualny_kurs > 0 and not loading_active:
        label_header.configure(
            text=tr("rate", rate=localized_number(aktualny_kurs, 4), code=aktualna_waluta)
        )
    else:
        label_header.configure(text=tr("loading_rate"))

    no_data_values = {TRANSLATIONS[language]["no_data"] for language in TRANSLATIONS}
    displayed_date = tr("no_data") if data_aktualizacji in no_data_values else data_aktualizacji
    if aktualny_kurs == 0:
        displayed_date = tr("loading")
    label_update.configure(text=tr("update", date=displayed_date))
    label_pln.configure(text=tr("amount_pln"))
    label_waluta.configure(
        text=tr("amount_foreign", symbol=symbol_waluty[aktualna_waluta])
    )
    button_pln.configure(text=tr("convert_to", symbol=symbol_waluty[aktualna_waluta]))
    button_waluta.configure(text=tr("convert_pln"))
    copy_button_pln.configure(text=tr("copy"))
    copy_button_waluta.configure(text=tr("copy"))
    reformat_result_label(label_waluta_result, symbol_waluty[aktualna_waluta])
    reformat_result_label(label_pln_result, "zł" if current_language == "pl" else "PLN")
    calculator_title.configure(text=tr("calculator"))
    calculator_history_info.configure(text=tr("history"))
    calculator_copy_button.configure(text=tr("copy_currency"))
    top_btn.configure(text=f"{tr('pin')}: {'ON' if is_topmost else 'OFF'}")
    support_button.configure(text=tr("support"))
    about_btn.configure(text=tr("about"))
    ukryj_dymek_aktualizacji()
    ukryj_dymek_kwoty()
    odswiez_wyswietlacz_kalkulatora()
    odswiez_historie_kalkulatora()


language_selector = ctk.CTkSegmentedButton(
    main_content,
    values=["PL", "EN"],
    width=76,
    height=28,
    corner_radius=8,
    border_width=1,
    fg_color=COLOR_INPUT,
    selected_color=COLOR_ACCENT,
    selected_hover_color=COLOR_ACCENT_HOVER,
    unselected_color=COLOR_INPUT,
    unselected_hover_color=COLOR_CARD_HOVER,
    text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 10, "bold"),
    command=change_language,
)
language_selector.place(x=590, y=28, anchor="ne")
language_selector.set("PL")

root.after(150, lambda: ustaw_walute("EUR"))
root.bind("<KeyPress>", obsluz_klawiature_kalkulatora)
root.bind_all("<Button-1>", zamknij_historie_po_kliknieciu_tla, add="+")
root.mainloop()
