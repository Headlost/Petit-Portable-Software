import tkinter as tk
import customtkinter as ctk
import requests
import winsound
import datetime
import os
import sys
import threading
from app_common import apply_window_icon, open_support_page, styled_messagebox as messagebox

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

APP_TITLE = "Przelicznik walut $ / € → PLN"
APP_VERSION = "4.0.0"
APP_AUTHOR = "Beniamin Żak"
APP_DESCRIPTION = "Przelicza kwoty USD i EUR na PLN według średnich kursów NBP."


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
        return 4.50, "brak danych", str(e)


def tekst_statusu_danych(data_kursu_z_czasem, dzis=None):
    """Zwraca krótką informację o aktualności tabeli kursów NBP."""
    try:
        data_kursu = datetime.date.fromisoformat(data_kursu_z_czasem.split()[0])
        dzis = dzis or datetime.date.today()
        if data_kursu == dzis:
            return "Najświeższe dane z NBP"
        if data_kursu < dzis:
            return (
                f"Dane NBP z {data_kursu.strftime('%d.%m.%Y')}. "
                "Kolejna aktualizacja w najbliższy dzień roboczy."
            )
        return "Data danych NBP jest późniejsza niż data systemowa"
    except (ValueError, IndexError):
        return "Brak aktualnych danych z NBP — użyto kursu awaryjnego"

# Przeliczanie walut
def przelicz_na_walute(event=None):
    global aktualny_kurs, aktualna_waluta
    try:
        pln = float(entry_pln.get().replace(",", "."))
        wynik = pln / aktualny_kurs
        label_waluta_result.configure(
            text=f"{wynik:.2f}".replace(".", ",") + f" {symbol_waluty[aktualna_waluta]}"
        )
    except ValueError:
        messagebox.showerror("Błąd", "Wprowadź poprawną kwotę w zł.")

def przelicz_na_pln(event=None):
    global aktualny_kurs, aktualna_waluta
    try:
        kwota = float(entry_waluta.get().replace(",", "."))
        wynik = kwota * aktualny_kurs
        label_pln_result.configure(
            text=f"{wynik:.2f}".replace(".", ",") + " zł"
        )
    except ValueError:
        messagebox.showerror("Błąd", f"Wprowadź poprawną kwotę w {symbol_waluty[aktualna_waluta]}.")

def skopiuj_wynik(label):
    wynik = label.cget("text").strip()
    if wynik:
        if wynik.endswith(" zł"):
            numeric_value = wynik[:-3].strip()
            root.clipboard_clear()
            root.clipboard_append(numeric_value)
        else:
            root.clipboard_clear()
            root.clipboard_append(wynik)
        winsound.MessageBeep(winsound.MB_ICONASTERISK)

# Informacje
def pokaz_informacje_o_autorze():
    messagebox.showinfo(
        "O mnie",
        f"Nazwa: {APP_TITLE}\nWersja: {APP_VERSION}\nAutor: {APP_AUTHOR}\n\n{APP_DESCRIPTION}",
    )

# Ustawienie waluty i kursu
symbol_waluty = {"EUR": "€", "USD": "$"}
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


def rozpocznij_ladowanie():
    global loading_active, spinner_frame_index
    loading_active = True
    spinner_frame_index = 0
    selector.configure(state="disabled")
    loading_label.place(relx=0.95, rely=0.72, anchor="center")
    animuj_ladowanie()


def zakoncz_ladowanie():
    global loading_active
    loading_active = False
    loading_label.place_forget()
    selector.configure(state="normal")


def zastosuj_nowy_kurs(waluta, kurs, data, blad):
    global aktualna_waluta, aktualny_kurs, data_aktualizacji
    aktualna_waluta = waluta
    aktualny_kurs = kurs
    data_aktualizacji = data
    label_header.configure(
        text=(f"Aktualny kurs: {aktualny_kurs:.4f}".replace(".", ",") + f" PLN za 1 {waluta}")
    )
    label_update.configure(text=f"Aktualizacja: {data_aktualizacji}")
    label_pln.configure(text="Kwota w zł")
    label_waluta.configure(text=f"Kwota w {symbol_waluty[waluta]}")
    button_pln.configure(text=f"Przelicz na {symbol_waluty[waluta]}")
    button_waluta.configure(text="Przelicz na zł")
    label_waluta_result.configure(text="—")
    label_pln_result.configure(text="—")
    entry_pln.delete(0, tk.END)
    entry_waluta.delete(0, tk.END)
    zakoncz_ladowanie()
    if blad:
        messagebox.showwarning(
            "Błąd",
            f"Nie udało się pobrać aktualnego kursu {waluta}: {blad}.\n"
            f"Użyto kursu awaryjnego: 4.50 PLN za 1 {waluta}",
        )

def ustaw_walute(waluta):
    rozpocznij_ladowanie()

    def pobierz_w_tle():
        wynik = pobierz_sredni_kurs(waluta)
        root.after(0, lambda: zastosuj_nowy_kurs(waluta, *wynik))

    threading.Thread(target=pobierz_w_tle, daemon=True).start()

# --- GUI ---
root = ctk.CTk()
root.title(APP_TITLE)
root.geometry("620x740")
root.resizable(False, False)
root.configure(fg_color=COLOR_WINDOW)
apply_window_icon(root)

# Flaga always-on-top
is_topmost = False

def toggle_topmost():
    global is_topmost
    is_topmost = not is_topmost
    root.attributes('-topmost', is_topmost)
    top_btn.configure(
        text=f"Przypnij: {'ON' if is_topmost else 'OFF'}",
        fg_color=COLOR_ACCENT if is_topmost else COLOR_INPUT,
        hover_color=COLOR_ACCENT_HOVER if is_topmost else COLOR_CARD_HOVER,
        text_color=COLOR_ACCENT_TEXT if is_topmost else COLOR_TEXT,
    )

# Ustawienia początkowe waluty
aktualna_waluta = "EUR"
aktualny_kurs = 0.0
data_aktualizacji = "pobieranie..."

ctk.CTkLabel(root, text="Przelicznik walut $ / € → PLN",
             text_color=COLOR_TEXT,
             font=ctk.CTkFont("Segoe UI", 28, "bold")).pack(
                 anchor="w", padx=30, pady=(26, 8))
ctk.CTkLabel(root, text="Aktualne średnie kursy Narodowego Banku Polskiego",
             text_color=COLOR_MUTED).pack(anchor="w", padx=30, pady=(0, 16))

selector = ctk.CTkSegmentedButton(
    root,
    values=["EUR", "USD"],
    command=ustaw_walute,
    fg_color=COLOR_INPUT,
    selected_color=COLOR_ACCENT,
    selected_hover_color=COLOR_ACCENT_HOVER,
    unselected_color=COLOR_INPUT,
    unselected_hover_color=COLOR_CARD_HOVER,
    text_color=COLOR_TEXT,
)
selector.set("EUR")
selector.pack(fill="x", padx=30, pady=(0, 16))

rate_card = ctk.CTkFrame(root, corner_radius=18, fg_color=COLOR_CARD)
rate_card.pack(fill="x", padx=30, pady=(0, 16))
label_header = ctk.CTkLabel(
    rate_card,
    text="Pobieranie aktualnego kursu...",
    text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 18, "bold"))
label_header.pack(pady=(18, 4))
label_update = ctk.CTkLabel(rate_card, text=f"Aktualizacja: {data_aktualizacji}", text_color=COLOR_MUTED)
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
        root,
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
        text="Kwota automatycznie zaokrąglona do 2 miejsc po przecinku",
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

frame_pln = ctk.CTkFrame(root, corner_radius=18, fg_color=COLOR_CARD)
frame_pln.pack(fill="x", padx=30, pady=8)
frame_pln.grid_columnconfigure(0, weight=1)
label_pln = ctk.CTkLabel(
    frame_pln, text="Kwota w zł", font=ctk.CTkFont("Segoe UI", 15, "bold"),
)
label_pln.grid(row=0, column=0, columnspan=2, padx=20, pady=(16, 6), sticky="w")
entry_pln = ctk.CTkEntry(
    frame_pln, height=40, placeholder_text="0,00", fg_color=COLOR_INPUT,
    border_color=COLOR_BORDER, text_color=COLOR_TEXT,
    font=ctk.CTkFont("Segoe UI", 17),
)
entry_pln.grid(row=1, column=0, padx=(20, 8), pady=6, sticky="ew")
entry_pln.bind("<Return>", przelicz_na_walute)
button_pln = ctk.CTkButton(frame_pln, text=f"Przelicz na {symbol_waluty[aktualna_waluta]}",
                           height=40, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                           text_color=COLOR_ACCENT_TEXT, command=przelicz_na_walute)
button_pln.grid(row=1, column=1, padx=(0, 20), pady=6)
label_waluta_result = ctk.CTkLabel(frame_pln, text="—", font=ctk.CTkFont("Segoe UI", 22, "bold"))
label_waluta_result.grid(row=2, column=0, padx=20, pady=(10, 18), sticky="w")
label_waluta_result.bind("<Enter>", lambda event: pokaz_dymek_kwoty(label_waluta_result))
label_waluta_result.bind("<Leave>", ukryj_dymek_kwoty)
ctk.CTkButton(frame_pln, text="Kopiuj", width=90, fg_color=COLOR_INPUT,
              hover_color=COLOR_CARD_HOVER, border_color=COLOR_BORDER, border_width=1,
              command=lambda: skopiuj_wynik(label_waluta_result)).grid(
                  row=2, column=1, padx=(0, 20), pady=(10, 18))

frame_waluta = ctk.CTkFrame(root, corner_radius=18, fg_color=COLOR_CARD)
frame_waluta.pack(fill="x", padx=30, pady=8)
frame_waluta.grid_columnconfigure(0, weight=1)
label_waluta = ctk.CTkLabel(
    frame_waluta,
    text=f"Kwota w {symbol_waluty[aktualna_waluta]}",
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
    frame_waluta, text="Przelicz na zł", height=40, fg_color=COLOR_ACCENT,
    hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_ACCENT_TEXT, command=przelicz_na_pln,
)
button_waluta.grid(row=1, column=1, padx=(0, 20), pady=6)
label_pln_result = ctk.CTkLabel(frame_waluta, text="—", font=ctk.CTkFont("Segoe UI", 22, "bold"))
label_pln_result.grid(row=2, column=0, padx=20, pady=(10, 18), sticky="w")
label_pln_result.bind("<Enter>", lambda event: pokaz_dymek_kwoty(label_pln_result))
label_pln_result.bind("<Leave>", ukryj_dymek_kwoty)
ctk.CTkButton(frame_waluta, text="Kopiuj", width=90, fg_color=COLOR_INPUT,
              hover_color=COLOR_CARD_HOVER, border_color=COLOR_BORDER, border_width=1,
              command=lambda: skopiuj_wynik(label_pln_result)).grid(
                  row=2, column=1, padx=(0, 20), pady=(10, 18))

footer = ctk.CTkFrame(root, fg_color="transparent")
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
    footer, text="Przypnij: OFF", command=toggle_topmost, **footer_button_style,
)
top_btn.grid(row=0, column=0, pady=(0, 6), sticky="w")
ctk.CTkButton(
    footer, text="Wsparcie  ♥", command=open_support_page, **footer_button_style,
).grid(row=1, column=0, sticky="w")
ctk.CTkButton(
    footer, text="O mnie", command=pokaz_informacje_o_autorze, **footer_button_style,
).grid(row=1, column=2, sticky="e")

root.after(150, lambda: ustaw_walute("EUR"))
root.mainloop()
