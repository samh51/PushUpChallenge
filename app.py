import streamlit as st
import pandas as pd
import time
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURATION ---
GOAL = 10000
SHEET_ID = "1EYEj7wC8Rdo2gCDP4__PQwknmvX75Y9PRkoDKqA8AUM"

# 🖼️ BILD KONFIGURATION
IMG_FIRST  = "https://media.istockphoto.com/id/1007282190/vector/horse-power-flame.jpg?s=612x612&w=0&k=20&c=uHnnvMTzaatfPblbFHdfhuJT7qLwsARF90oqH0dMCjA="
IMG_MIDDLE = "https://t3.ftcdn.net/jpg/02/11/11/34/360_F_211113432_Gb89carZwwGuJA6lmux3NBU9tes3efMk.jpg"
IMG_LAST   = "https://i.etsystatic.com/28959621/r/il/e2cf08/5908874106/il_570xN.5908874106_80rl.jpg"

# --- PAGE SETUP ---
st.set_page_config(page_title="Pushup Derby", page_icon="🐎", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .racetrack { 
        background-color: #3e4a38; 
        padding: 10px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        position: relative; /* Für absolute Positionierung des Datums */
    }
    .lane { border-bottom: 3px dashed #6b7c62; padding: 20px 0; position: relative; height: 140px; }
    .horse-container { position: absolute; top: 10px; transition: left 0.5s ease-in-out; z-index: 10; text-align: center; width: 120px; transform: translateX(-50%); }
    .race-img { width: 100px; height: 100px; object-fit: contain; filter: drop-shadow(0px 4px 4px rgba(0,0,0,0.5)); background-color: transparent; border-radius: 10px; }
    .name-tag { display: block; font-size: 16px; font-weight: bold; color: white; background: rgba(0,0,0,0.7); padding: 4px 10px; border-radius: 6px; margin-top: -5px; white-space: nowrap; }
    .finish-line { position: absolute; right: 0; top: 0; bottom: 0; width: 15px; background-image: repeating-linear-gradient(45deg, #000, #000 10px, #fff 10px, #fff 20px); opacity: 0.6; z-index: 0; }
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    
    /* NEU: Datumsanzeige */
    .date-display {
        position: absolute;
        top: 10px;
        right: 15px;
        background-color: rgba(255, 255, 255, 0.8);
        color: #333;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        font-family: monospace;
        z-index: 100;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- VERBINDUNGS-FUNKTIONEN ---
def get_google_sheet_client():
    try:
        if "service_account" not in st.secrets:
            st.error("Secrets Error: The [service_account] section is missing from secrets.toml.")
            st.stop()
        secrets = st.secrets["service_account"]
        creds = Credentials.from_service_account_info(
            secrets, scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"🔐 Authentication Error: {e}")
        st.stop()

def get_data(tab_index):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.get_worksheet(tab_index)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Error loading Tab Index {tab_index}: {e}")
        return pd.DataFrame()

def update_single_entry(name, new_reps):
    """Fügt einen einzelnen Eintrag hinzu (für das schnelle Loggen)"""
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        
        # 1. Totals aktualisieren
        ws_totals = sheet.get_worksheet(0)
        cell = ws_totals.find(name)
        if cell:
            current_val = int(ws_totals.cell(cell.row, 2).value or 0)
            ws_totals.update_cell(cell.row, 2, current_val + new_reps)
        
        # 2. Log Eintrag hinzufügen
        ws_logs = sheet.get_worksheet(1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws_logs.append_row([timestamp, name, new_reps])
        return True
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False

def save_full_edits(edited_logs_df):
    """
    Überschreibt das Logbuch mit den bearbeiteten Daten 
    und berechnet die Totals komplett neu.
    """
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        
        # 1. Logs überschreiben (Tab 1)
        ws_logs = sheet.get_worksheet(1)
        ws_logs.clear()
        # Header + Daten schreiben
        data_to_write = [edited_logs_df.columns.values.tolist()] + edited_logs_df.values.tolist()
        ws_logs.update(data_to_write)
        
        # 2. Totals neu berechnen
        # Gruppieren nach Name und Summe bilden
        edited_logs_df['Amount'] = pd.to_numeric(edited_logs_df['Amount'], errors='coerce').fillna(0)
        new_totals = edited_logs_df.groupby('Name')['Amount'].sum().reset_index()
        
        # Sicherstellen, dass alle Namen existieren (auch wenn Summe 0 ist)
        all_names = ["Kevin", "Sämi", "Eric", "Elia"]
        final_totals = pd.DataFrame({'Name': all_names, 'Pushups': 0})
        
        # Merge mit den echten Daten
        for index, row in new_totals.iterrows():
            idx = final_totals.index[final_totals['Name'] == row['Name']].tolist()
            if idx:
                final_totals.at[idx[0], 'Pushups'] = row['Pushups']
        
        # 3. Totals überschreiben (Tab 0)
        ws_totals = sheet.get_worksheet(0)
        ws_totals.clear()
        totals_data = [final_totals.columns.values.tolist()] + final_totals.values.tolist()
        ws_totals.update(totals_data)
        
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern der Änderungen: {e}")
        return False

# --- RENDER FUNKTION ---
def render_track_html(current_df, display_date=None):
    if current_df.empty: return ""
    
    if 'Pushups' in current_df.columns:
        current_df['Pushups'] = pd.to_numeric(current_df['Pushups'], errors='coerce').fillna(0)
    
    df_sorted = current_df.sort_values('Pushups', ascending=False)
    leader_name = df_sorted.iloc[0]['Name']
    last_place_name = df_sorted.iloc[-1]['Name']
    
    # HTML Start
    track_html = '<div class="racetrack">'
    
    # NEU: Datum einfügen, falls vorhanden
    if display_date:
        track_html += f'<div class="date-display">📅 {display_date}</div>'
    
    all_names = ["Kevin", "Sämi", "Eric", "Elia"] 
    
    for name in all_names:
        user_row = current_df[current_df['Name'] == name]
        raw_score = user_row.iloc[0]['Pushups'] if not user_row.empty else 0
        progress = min(90, (raw_score / GOAL) * 100)
        
        if name == leader_name and raw_score > 0:
            current_icon = IMG_FIRST
        elif name == last_place_name and raw_score > 0:
            current_icon = IMG_LAST
        else:
            current_icon = IMG_MIDDLE
            
        track_html += f"""
<div class="lane">
    <div class="finish-line"></div>
    <div class="horse-container" style="left: {progress}%;">
        <img src="{current_icon}" class="race-img">
        <span class="name-tag">{name} ({int(raw_score)})</span>
    </div>
</div>
"""
    track_html += '</div>'
    return track_html

# --- MAIN APP ---
st.title("🐎 10k Pushup Derby")

race_placeholder = st.empty()

if 'has_animated' not in st.session_state:
    st.session_state.has_animated = False

# --- LOAD DATA ---
df_totals = get_data(0)
df_logs = get_data(1)

if df_totals.empty:
    st.warning("Warte auf Daten...")
    st.stop()

# --- ANIMATION LOGIC ---
if not st.session_state.has_animated and not df_logs.empty:
    
    # 1. Startlinie
    all_names = ["Kevin", "Sämi", "Eric", "Elia"]
    race_scores = {name: 0 for name in all_names}
    
    initial_df = pd.DataFrame([{'Name': n, 'Pushups': 0} for n in all_names])
    race_placeholder.markdown(render_track_html(initial_df, "Start"), unsafe_allow_html=True)
    time.sleep(0.8)
    
    # 2. Logs sortieren
    if 'Timestamp' in df_logs.columns:
        df_logs['Timestamp'] = pd.to_datetime(df_logs['Timestamp'], errors='coerce')
        df_logs = df_logs.sort_values('Timestamp')
    
    if 'Amount' in df_logs.columns:
        df_logs['Amount'] = pd.to_numeric(df_logs['Amount'], errors='coerce').fillna(0)
        
        # 3. REPLAY LOOP
        for index, row in df_logs.iterrows():
            name = row['Name']
            amount = row['Amount']
            # Datum formatieren (z.B. 12.05.2024)
            current_ts = row['Timestamp']
            date_str = current_ts.strftime('%d.%m.%Y') if pd.notnull(current_ts) else ""
            
            if name in race_scores:
                race_scores[name] += amount
            
            # DataFrame für Renderer
            frame_data = [{'Name': n, 'Pushups': s} for n, s in race_scores.items()]
            frame_df = pd.DataFrame(frame_data)
            
            # Render mit DATUM
            race_placeholder.markdown(render_track_html(frame_df, display_date=date_str), unsafe_allow_html=True)
            time.sleep(0.5)

    st.session_state.has_animated = True

# --- FINAL STATE ---
# Aktuelles Datum für den Endstand
today_str = datetime.now().strftime('%d.%m.%Y')
race_placeholder.markdown(render_track_html(df_totals, today_str), unsafe_allow_html=True)

# 2. STATISTIKEN
df_sorted = df_totals.sort_values('Pushups', ascending=False)
leader = df_sorted.iloc[0]
remaining = GOAL - leader['Pushups']

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🏆 Leader</h3>
        <h2>{leader['Name']}</h2>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🏁 To Win</h3>
        <h2>{int(remaining) if remaining > 0 else 0}</h2>
    </div>
    """, unsafe_allow_html=True)

# 3. EINGABE FORMULAR
st.divider()
st.subheader("Log Your Reps")

with st.form("log_form", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    names_list = ["Kevin", "Sämi", "Eric", "Elia"]
    
    with col_a:
        who = st.selectbox("Wer bist du?", names_list)
    with col_b:
        amount = st.number_input("Anzahl Pushups:", min_value=1, value=20, step=1)
    
    submitted = st.form_submit_button("🚀 Eintragen", use_container_width=True)

    if submitted:
        with st.spinner("Speichere..."):
            success = update_single_entry(who, amount)
            if success:
                st.success(f"{amount} Pushups für {who} eingetragen!")
                time.sleep(1)
                st.rerun()

# 4. ADMIN / BEARBEITEN BEREICH
st.divider()
with st.expander("📝 Protokoll bearbeiten / Fehler korrigieren"):
    st.warning("Achtung: Hier kannst du Einträge löschen oder ändern. Das ändert den Spielstand direkt!")
    
    if not df_logs.empty:
        # Wir machen eine Kopie, damit der Editor sauber arbeitet
        editable_df = df_logs.copy()
        
        # Konvertiere Timestamp zu String für bessere Lesbarkeit im Editor
        if 'Timestamp' in editable_df.columns:
            editable_df['Timestamp'] = editable_df['Timestamp'].astype(str)

        # Der Editor: num_rows="dynamic" erlaubt Löschen/Hinzufügen
        edited_df = st.data_editor(
            editable_df, 
            num_rows="dynamic", 
            use_container_width=True,
            key="log_editor"
        )
        
        if st.button("💾 Änderungen speichern (Datenbank überschreiben)"):
            with st.spinner("Berechne Totals neu und speichere..."):
                if save_full_edits(edited_df):
                    st.success("Erfolgreich gespeichert! Seite wird neu geladen.")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("Noch keine Einträge vorhanden.")

st.caption("Data is live-synced with Google Sheets via gspread.")
