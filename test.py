import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import timedelta, date
from streamlit_calendar import calendar
from currency_converter import CurrencyConverter

st.title("💸 Budget Splitter")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def check_password():
    """Prüft das Passwort und aktualisiert den Status"""
    # Wir holen das Passwort aus dem Eingabefeld
    entered_password = st.session_state["password_input"]
    
    # Wir vergleichen es mit dem Passwort in den Secrets
    if entered_password == st.secrets["app_password"]:
        st.session_state.logged_in = True
        # Passwort aus dem Speicher löschen (Sicherheit)
        del st.session_state["password_input"]
    else:
        st.error("Falsches Passwort! 🚫")

# 2. Wenn NICHT eingeloggt -> Zeige nur das Login-Feld
if not st.session_state.logged_in:
    st.text_input(
        "Bitte Passwort eingeben:", 
        type="password",  # Versteckt die Zeichen als Punkte
        key="password_input", 
        on_change=check_password # Führt die Prüfung aus, wenn man Enter drückt
    )
    # WICHTIG: Hier stoppen wir alles Weitere!
    st.stop()

c = CurrencyConverter()

# 1. Verbindung herstellen
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Bestehende Daten laden (ttl=0 verhindert, dass alte Daten im Cache bleiben)
data = conn.read(worksheet="Calendar", ttl=600)

df_config = conn.read(worksheet="Globals", ttl=600)
external_budget_alina = float(df_config[df_config["Key"] == "ExternalBudgetAlina"]["Value"].iloc[0])
budget_delta_alina = float(df_config[df_config["Key"] == "DeltaAlina"]["Value"].iloc[0])
external_budget_pius = float(df_config[df_config["Key"] == "ExternalBudgetPius"]["Value"].iloc[0])
budget_delta_pius = float(df_config[df_config["Key"] == "DeltaPius"]["Value"].iloc[0])
latest_date = date.fromisoformat(df_config[df_config["Key"] == "LatestDate"]["Value"].iloc[0])

today = date.fromisoformat("2026-01-16")

if today > latest_date:
    anzahl_tage = (today - latest_date).days
    current_date = latest_date
    delta_alina = 0
    delta_pius = 0
    for _ in range(anzahl_tage):
        mask = data["Datum"] == current_date.strftime("%Y-%m-%d")
        delta_alina += data.loc[mask, "Alina"]
        delta_pius += data.loc[mask, "Pius"]
        delta_alina_last = data.loc[mask, "Alina"]
        delta_pius_last = data.loc[mask, "Pius"]
    updated_config = df_config.copy()
    mask1 = updated_config["Key"] == "ExternalBudgetPius"
    mask2 = updated_config["Key"] == "ExternalBudgetAlina"
    mask3 = updated_config["Key"] == "DeltaAlina"
    mask4 = updated_config["Key"] == "DeltaPius"
    mask5 = updated_config["Key"] == "LatestDate"
    updated_config.loc[mask1, "Value"] += float(delta_pius)
    updated_config.loc[mask2, "Value"] += float(delta_alina)
    updated_config.loc[mask3, "Value"] = float(delta_alina_last)
    updated_config.loc[mask4, "Value"] = float(delta_pius_last)
    updated_config.loc[mask5, "Value"] = today
    conn.update(worksheet="Globals", data=updated_config)
    st.cache_data.clear()
    st.rerun()

farben = {
  "Thailand": "#ffb3b3",
  "Singapur": "#ffe0b3",
  "Bali": "#d9b3ff",
  "Australien": "#b3d1ff",
  "Neuseeland": "#b3e6cc",
  "Vanuatu": "#ffff4d",
}

tab_kalender, tab_eintragen = st.tabs(["📅 Kalender & Übersicht", "➕ Kosten hinzufügen"])

#st.subheader("Dein Budget-Kalender 🗓️")
with tab_kalender:
# 1. Daten für den Kalender umwandeln
    calendar_events = []

    for index, row in data.iterrows():
        calendar_events.append({
            "title": f"{row['Alina']}€",  # Was im Kalender steht
            "start": row["Datum"],          # Das Datum (Format YYYY-MM-DD passt perfekt)
            "end": row["Datum"],
            "allDay": True,                 # Ganztägiges Event
            # Optional: Tooltip mit der Beschreibung, wenn man mit der Maus drüber fährt
            "backgroundColor": "#ff0000",
            "borderColor": "#ff0000",
        })
        calendar_events.append({
            "title": f"{row['Pius']}€",  # Was im Kalender steht
            "start": row["Datum"],          # Das Datum (Format YYYY-MM-DD passt perfekt)
            "end": row["Datum"],
            "allDay": True,                 # Ganztägiges Event
            # Optional: Tooltip mit der Beschreibung, wenn man mit der Maus drüber fährt
            "backgroundColor": "#0000ff",
            "borderColor": "#0000ff",
        })
        calendar_events.append({
            "display": "background",
            "backgroundColor": farben[row["Land"]],
            "title": f"{row['Land']}",  # Was im Kalender steht
            "start": row["Datum"],          # Das Datum (Format YYYY-MM-DD passt perfekt)
            "end": row["Datum"],
        })

    # 2. Kalender Optionen (Aussehen anpassen)
    calendar_options = {
        "editable": False,         # User kann Drag&Drop im Kalender machen? (erstmal aus)
        "navLinks": True,          # Klick auf Tag springt zur Tagesansicht
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,listMonth" # Umschalter Monat / Liste
        },
        "initialDate": "2026-01-14", # Startdatum deiner Reise
        "locale": "de",
        "height": "850px",
    }

    # 3. Kalender anzeigen
    custom_css = """
        .fc-event-title {
            font-weight: bold;
        }
    """

    calendar = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)

    # Optional: Wenn man auf ein Event klickt, Details anzeigen
    if calendar.get("eventClick"):
        event_data = calendar["eventClick"]["event"]
        # Prüfen, ob es ein normales Event ist (Background events haben oft keine extendedProps)
        if "extendedProps" in event_data:
            props = event_data["extendedProps"]
            st.info(f"Details zum {event_data['start']}: {props.get('description', '')}")

    col1, col2 = st.columns(2)
    col1.metric("Externes Budget Alina", f"{external_budget_alina}€", f"{budget_delta_alina}€", border=True)
    col2.metric("Externes Budget Pius", f"{external_budget_pius}€", f"{budget_delta_pius}€", border=True)

#st.divider()





# 3. Das Eingabe-Formular
#st.subheader("Neue Kosten eintragen")
with tab_eintragen:

    with st.form("entry_form"):
        beschreibung = st.selectbox("Art der Ausgabe", ("Übernachtung", "Essen", "Transport", "Aktivitäten", "Orga", "Sonstiges"))
        col_amt, col_curr= st.columns([3, 1])
        with col_curr:
            # Währungsauswahl (Du kannst hier mehr hinzufügen)
            waehrung = st.selectbox("Währung", ["EUR", "USD", "THB", "SGD", "IDR", "AUD", "NZD"])
        
        with col_amt:
            gesamt_betrag = st.number_input("Betrag (in Original-Währung)", min_value=0.0, step=1.0)


        #gesamt_betrag = st.number_input("Gesamtkosten (€)", min_value=0.0, step=1.0)
        person = st.selectbox("Ausgabe für", ("Beide", "Jeweils", "Alina", "Pius"))
        zahler = st.selectbox("Bezahlt von", ("Alina", "Pius", "Split"))
        
        # Datumsauswahl (Zeitraum)
        #col1, col2 = st.columns(2)
        start_datum, end_datum = st.date_input("Zeitraum", value=(date.today(), date.today()))
        #end_datum = col2.date_input("Bis", value=date.today())
        
        submit_button = st.form_submit_button("Kosten aufteilen & Speichern")

        if submit_button:
            if end_datum < start_datum:
                st.error("Fehler: Das Enddatum muss nach dem Startdatum liegen!")
            elif gesamt_betrag == 0:
                st.error("Bitte einen Betrag eingeben.")
            else:
                # --- Die Logik zum Aufteilen ---
                if waehrung == "EUR":
                    final_euro_amount = gesamt_betrag
                else:
                    try:
                        # convert(Menge, VON, NACH)
                        final_euro_amount = c.convert(gesamt_betrag, waehrung, "EUR")
                    except:
                        st.error(f"Kein Kurs für {waehrung} gefunden. Bitte manuellen Kurs nutzen.")
                        st.stop()
                
                # Anzahl der Tage berechnen (inklusive Start- und Endtag)
                anzahl_tage = (end_datum - start_datum).days + 1
                
                # Kosten pro Tag berechnen
                kosten_pro_tag = round(final_euro_amount / anzahl_tage, 2)
                
                st.info(f"Zeitraum: {anzahl_tage} Tage. Kosten pro Tag: {kosten_pro_tag}€")

                updated_df = data.copy()
                match_found = False
                
                # Loop durch die gewählten Tage
                current_date = start_datum
                for _ in range(anzahl_tage):
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    # --- DIE WICHTIGE ÄNDERUNG ---
                    # Suche die Zeile, wo das Datum übereinstimmt
                    mask = updated_df["Datum"] == date_str
                    
                    if mask.any():
                        match_found = True
                        
                        if person == "Beide":
                            updated_df.loc[mask, "Alina"] -= kosten_pro_tag/2
                            updated_df.loc[mask, "Pius"] -= kosten_pro_tag/2
                            updated_df.loc[mask, beschreibung] += kosten_pro_tag/2
                        elif person == "Jeweils":
                            updated_df.loc[mask, "Alina"] -= kosten_pro_tag
                            updated_df.loc[mask, "Pius"] -= kosten_pro_tag
                            updated_df.loc[mask, beschreibung] += kosten_pro_tag
                        elif person == "Alina":                    
                            updated_df.loc[mask, "Alina"] -= kosten_pro_tag                      
                            updated_df.loc[mask, beschreibung] += kosten_pro_tag
                        else:
                            updated_df.loc[mask, "Pius"] -= kosten_pro_tag
                            updated_df.loc[mask, beschreibung] += kosten_pro_tag
                    
                    current_date += timedelta(days=1)
                
                if match_found:
                    # Update zu Google senden
                    conn.update(data=updated_df)
                    st.success(f"Gespeichert! {kosten_pro_tag}€ pro Tag hinzugefügt.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Keine passenden Tage in der Tabelle gefunden! Liegt das Datum zwischen 14.01.26 und 25.04.26?")

with st.sidebar:
    if st.button("🔄 Daten aktualisieren"):
        st.cache_data.clear()
        st.rerun()

    st.header("💱 Währungs-Check")
    
    # Kleine Spalten für die Eingabe
    col1, col2 = st.columns(2)
    amount = st.number_input("Betrag", value=1.0, step=1.0)
    base_curr = col1.selectbox("Von", ["EUR", "USD", "THB", "SGD", "IDR", "AUD", "NZD"])
    target_curr = col2.selectbox("Nach", ["EUR", "USD", "THB", "SGD", "IDR", "AUD", "NZD"], index=1)
    
    if base_curr != target_curr:
        result = c.convert(amount, base_curr, target_curr)
        st.write(f"**{amount} {base_curr} = {result:.2f} {target_curr}**")
        
        # Den reinen Kurs anzeigen
        single_rate = c.convert(1, base_curr, target_curr)
        st.caption(f"Kurs: 1 {base_curr} = {single_rate:.4f} {target_curr}")