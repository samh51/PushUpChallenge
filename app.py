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

# --- PROFI DESIGN CSS ---
st.markdown("""
    <style>
    /* Das Haupt-Stadion */
    .racetrack { 
        /* Schöner Rasen-Verlauf statt flacher Farbe */
        background: linear-gradient(180deg, #2d3b26 0%, #3e4a38 100%);
        border: 8px solid #5d4037; /* Holz/Erde Rahmen */
        border-radius: 15px; 
        margin-bottom: 20px; 
        box-shadow: inset 0 0 20px rgba(0,0,0,0.6), 0 10px 20px rgba(0,0,0,0.3); 
        position: relative; 
        overflow: hidden;
        /* WICHTIG: Padding links/rechts verhindert, dass Pferde abgeschnitten werden */
        padding: 20px 60px 20px 60px; 
    }

    /* Die einzelnen Bahnen */
    .lane { 
        border-bottom: 2px dashed rgba(255,255,255,0.15); 
        padding: 15px 0; 
        position: relative; 
        height: 120px; 
        z-index: 5; 
    }

    /* Der Container, der sich bewegt */
    .horse-container { 
        position: absolute; 
        top: 15px; 
        transition: left 0.5s cubic-bezier(0.25, 1, 0.5, 1); /* Weichere Animation */
        z-index: 20; 
        text-align: center; 
        width: 100px; 
        transform: translateX(-50%); /* Zentriert das Pferd auf dem Punkt */
    }

    /* Das Bild (Avatar Look) */
    .race-img { 
        width: 70px; 
        height: 70px; 
        object-fit: cover; /* Schneidet Bilder sauber zu */
        border-radius: 50%; /* Macht das Bild rund */
        border: 3px solid #fff; /* Weisser Rand */
        box-shadow: 0 4px 8px rgba(0,0,0,0.5); /* Schatten für 3D Effekt */
        background-color: #fff;
    }

    /* Das Namensschild */
    .name-tag { 
        display: inline-block;
        font-size: 12px; 
        font-weight: bold; 
        color: #333; 
        background: rgba(255,255,255,0.9); 
        padding: 2px 8px; 
        border-radius: 12px; /* Pillen-Form */
        margin-top: 5px; 
        white-space: nowrap;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    /* Startlinie */
    .start-line {
        position: absolute;
        left: 0; top: 0; bottom: 0; width: 4px;
        background-color: rgba(255,255,255,0.8);
        z-index: 15;
        box-shadow: 0 0 5px rgba(255,255,255,0.5);
    }

    /* Ziellinie (Schachbrett) */
    .finish-line { 
        position: absolute; 
        right: 0; top: 0; bottom: 0; width: 20px; 
        background-image: 
            linear-gradient(45deg, #000 25%, transparent 25%), 
            linear-gradient(-45deg, #000 25%, transparent 25%), 
            linear-gradient(45deg, transparent 75%, #000 75%), 
            linear-gradient(-45deg, transparent 75%, #000 75%);
        background-size: 10px 10px;
        background-color: #fff;
        opacity: 0.9; 
        z-index: 15; 
        box-shadow: -2px 0 5px rgba(0,0,0,0.3);
    }

    /* Meilensteine (Hintergrund) */
    .milestone-line {
        position: absolute;
        top: 0; bottom: 0;
        border-left: 1px solid rgba(255, 255, 255, 0.1); /* Sehr dezent */
        z-index: 1; 
    }
    .milestone-text {
        position: absolute;
        bottom: 5px;
        font-size: 9px;
        color: rgba(255, 255, 255, 0.3);
        transform: translateX(-50%); 
        font-family: sans-serif;
    }

    /* Datumsanzeige Oben Rechts */
    .date-display {
        position: absolute;
        top: 15px;
        right: 20px;
        background-color: rgba(0, 0, 0, 0.6);
        color: #fff;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-family: monospace;
        z-index: 100;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .metric-card { 
        background: linear-gradient(135deg, #f0f2f6 0%, #ffffff 100%);
        padding: 20px; 
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
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
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        ws_totals = sheet.get_worksheet(0)
        cell = ws_totals.find(name)
        if cell:
            current_val = int(ws_totals.cell(cell.row, 2).value or 0)
            ws_totals.update_cell(cell.row, 2, current_val + new_reps)
        
        ws_logs = sheet.get_worksheet(1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws_logs.append_row([timestamp, name, new_reps])
        return True
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False

def save_full_edits(edited_logs_df):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        
        ws_logs = sheet.get_worksheet(1)
        ws_logs.clear()
        data_to_write = [edited_logs_df.columns.values.tolist()] + edited_logs_df.values.tolist()
        ws_logs.update(data_to_write)
        
        edited_logs_df['Amount'] = pd.to_numeric(edited_logs_df['Amount'], errors='coerce').fillna(0)
        new_totals = edited_logs_df.groupby('Name')['Amount'].sum().reset_index()
        
        all_names = ["Kevin", "Sämi", "Eric", "Elia"]
        final_totals = pd.DataFrame({'Name': all_names, 'Pushups': 0})
        
        for index, row in new_totals.iterrows():
            idx = final_totals.index[final_totals['Name'] == row['Name']].tolist()
            if idx:
                final_totals.at[idx[0], 'Pushups'] = row['Amount']
        
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
    
    # Stadion Start
    track_html = '<div class="racetrack">'
    
    # Meilensteine
    for m in range(1000, GOAL, 1000):
        pct = (m / GOAL) * 100
        track_html += f"""
<div class="milestone-line" style="left: {pct}%;">
    <span class="milestone-text">{int(m/1000)}k</span>
</div>
"""
    # Datum
    if display_date:
        track_html += f'<div class="date-display">📅 {display_date}</div>'
    
    all_names = ["Kevin", "Sämi", "Eric", "Elia"] 
    
    for name in all_names:
        user_row = current_df[current_df['Name'] == name]
        raw_score = user_row.iloc[0]['Pushups'] if not user_row.empty else 0
        progress = min(100, (raw_score / GOAL) * 100) # Capped at 100%
        
        if name == leader_name and raw_score > 0:
            current_icon = IMG_FIRST
        elif name == last_place_name and raw_score > 0:
            current_icon = IMG_LAST
        else:
            current_icon = IMG_MIDDLE
            
        track_html += f"""
<div class="lane">
    <div class="start-line"></div>
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
    
    all_names = ["Kevin", "Sämi", "Eric", "Elia"]
    race_scores = {name: 0 for name in all_names}
    
    initial_df = pd.DataFrame([{'Name': n, 'Pushups': 0} for n in all_names])
    race_placeholder.markdown(render_track_html(initial_df, "Start"), unsafe_allow_html=True)
    time.sleep(0.8)
    
    if 'Timestamp' in df_logs.columns:
        df_logs['Timestamp'] = pd.to_datetime(df_logs['Timestamp'], errors='coerce')
        df_logs = df_logs.sort_values('Timestamp')
    
    if 'Amount' in df_logs.columns:
        df_logs['Amount'] = pd.to_numeric(df_logs['Amount'], errors='coerce').fillna(0)
        
        for index, row in df_logs.iterrows():
            name = row['Name']
            amount = row['Amount']
            current_ts = row['Timestamp']
            date_str = current_ts.strftime('%d.%m.%Y') if pd.notnull(current_ts) else ""
            
            if name in race_scores:
                race_scores[name] += amount
            
            frame_data = [{'Name': n, 'Pushups': s} for n, s in race_scores.items()]
            frame_df = pd.DataFrame(frame_data)
            
            race_placeholder.markdown(render_track_html(frame_df, display_date=date_str), unsafe_allow_html=True)
            time.sleep(0.5)

    st.session_state.has_animated = True

# --- FINAL STATE ---
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
        <h3 style="margin:0; font-size:16px; color:#666;">🏆 Leader</h3>
        <h2 style="margin:0; font-size:28px;">{leader['Name']}</h2>
        <p style="margin:0; color:#888;">{int(leader['Pushups'])} reps</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3 style="margin:0; font-size:16px; color:#666;">🏁 To Win</h3>
        <h2 style="margin:0; font-size:28px;">{int(remaining) if remaining > 0 else 0}</h2>
        <p style="margin:0; color:#888;">reps needed</p>
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
        editable_df = df_logs.copy()
        if 'Timestamp' in editable_df.columns:
            editable_df['Timestamp'] = editable_df['Timestamp'].astype(str)

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
