import streamlit as st
import pandas as pd
import time
import urllib.parse
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURATION ---
GOAL = 10000
SHEET_ID = "1EYEj7wC8Rdo2gCDP4__PQwknmvX75Y9PRkoDKqA8AUM"
EXERCISES = ["Pushups", "Pullups", "Dips"]

# 🖼️ BILD KONFIGURATION
IMG_FIRST  = "https://media.istockphoto.com/id/1007282190/vector/horse-power-flame.jpg?s=612x612&w=0&k=20&c=uHnnvMTzaatfPblbFHdfhuJT7qLwsARF90oqH0dMCjA="
IMG_MIDDLE = "https://t3.ftcdn.net/jpg/02/11/11/34/360_F_211113432_Gb89carZwwGuJA6lmux3NBU9tes3efMk.jpg"
IMG_LAST   = "https://i.etsystatic.com/28959621/r/il/e2cf08/5908874106/il_570xN.5908874106_80rl.jpg"

# --- PAGE SETUP ---
st.set_page_config(page_title="Fitness Derby", page_icon="🐎", layout="centered")

# --- PROFI DESIGN CSS ---
st.markdown("""
<style>
/* Das Haupt-Stadion */
.racetrack { 
    background: linear-gradient(180deg, #2d3b26 0%, #3e4a38 100%);
    border: 8px solid #5d4037; 
    border-radius: 15px; 
    margin-bottom: 20px; 
    box-shadow: inset 0 0 20px rgba(0,0,0,0.6), 0 10px 20px rgba(0,0,0,0.3); 
    position: relative; 
    overflow: hidden;
    padding: 60px 0px 40px 0px; 
}

.lane { 
    padding: 15px 0; 
    position: relative; 
    height: 120px; 
}

.lane-divider {
    position: absolute;
    left: 8.333%; right: 8.333%; 
    border-bottom-width: 2px;
    z-index: 1;
}

.horse-container { 
    position: absolute; 
    top: 15px; 
    transition: left 0.5s cubic-bezier(0.25, 1, 0.5, 1); 
    z-index: 20; 
    text-align: center; 
    width: 100px; 
    transform: translateX(-50%); 
}

.race-img { 
    width: 70px; 
    height: 70px; 
    object-fit: cover; 
    border-radius: 50%; 
    border: 3px solid #fff; 
    box-shadow: 0 4px 8px rgba(0,0,0,0.5); 
    background-color: #fff;
}

.name-tag { 
    display: inline-block;
    font-size: 12px; 
    font-weight: bold; 
    color: #333; 
    background: rgba(255,255,255,0.9); 
    padding: 2px 8px; 
    border-radius: 12px; 
    margin-top: 5px; 
    white-space: nowrap;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* GRID SYSTEM */
.grid-line-base {
    position: absolute;
    top: 60px; bottom: 40px; 
    pointer-events: none;
}

.grid-line {
    border-left: 1px dashed rgba(255, 255, 255, 0.25); 
    z-index: 2; 
}

.start-line-marker {
    border-left: 2px solid rgba(255, 255, 255, 0.6); 
    z-index: 3; 
}

.major-line {
    border-left: 3px solid rgba(255, 255, 255, 0.5); 
    z-index: 3; 
}

.finish-line-marker {
    width: 15px;
    background-image: 
    linear-gradient(45deg, #000 25%, transparent 25%), 
    linear-gradient(-45deg, #000 25%, transparent 25%), 
    linear-gradient(45deg, transparent 75%, #000 75%), 
    linear-gradient(-45deg, transparent 75%, #000 75%);
    background-size: 10px 10px;
    background-color: rgba(255,255,255,0.9);
    z-index: 4;
    transform: translateX(-50%);
}

.grid-text {
    position: absolute;
    bottom: -32px;
    font-size: 10px;
    color: rgba(255, 255, 255, 0.6);
    transform: translateX(-50%); 
    font-family: sans-serif;
    font-weight: bold;
    white-space: nowrap;
}

.grid-text-major {
    font-size: 12px;
    color: rgba(255, 255, 255, 1.0);
    bottom: -34px; 
}

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
    text-align: left; 
    margin-bottom: 10px; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border: 1px solid #e0e0e0;
    height: 100%; 
}

.leader-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #eee;
    font-size: 14px;
}
.leader-row:last-child { border-bottom: none; }

.rank-badge {
    background-color: #3e4a38;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    text-align: center;
    font-size: 12px;
    line-height: 24px;
    display: inline-block;
    margin-right: 10px;
    font-weight: bold;
}

.player-info { display: flex; flex-direction: column; }
.player-name { font-weight: bold; color: #333; }
.forecast-date { font-size: 11px; color: #888; margin-top: 2px; }
.score-display { font-size: 16px; font-weight: bold; color: #3e4a38; text-align: right; }
.score-detail { font-size: 10px; color: #888; font-weight: normal; display: block; }

.whatsapp-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background-color: #128C7E; 
    color: white !important;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 8px;
    text-decoration: none !important; 
    width: 100%;
    margin-top: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    font-family: sans-serif;
    transition: background-color 0.3s;
}
.whatsapp-btn:hover {
    background-color: #075E54;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    color: white !important;
    text-decoration: none !important;
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

# --- BATCH UPDATE FUNKTION ---
def update_batch_entry(name, input_pushups, input_pullups, input_dips):
    """Speichert alle 3 Übungen auf einmal und aktualisiert die Total-Spalte"""
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        ws_totals = sheet.get_worksheet(0)
        ws_logs = sheet.get_worksheet(1)
        
        # 1. Totals aktualisieren
        # Wir lesen die Zeile des Users, berechnen neu und schreiben zurück.
        # Spaltenstruktur in Sheet: A=Name, B=Total, C=Pushups, D=Pullups, E=Dips
        cell = ws_totals.find(name)
        if not cell:
            st.error(f"User {name} nicht gefunden!")
            return False, ""
            
        row_num = cell.row
        # Werte holen (Spalten C, D, E -> Index 3, 4, 5)
        # Wir holen die ganze Zeile (A bis E) als Liste
        row_values = ws_totals.row_values(row_num)
        
        # Sicherstellen, dass die Liste lang genug ist (falls Zellen leer sind)
        while len(row_values) < 5:
            row_values.append("0")
            
        current_pushups = int(row_values[2] or 0)
        current_pullups = int(row_values[3] or 0)
        current_dips = int(row_values[4] or 0)
        
        # Neue Summen berechnen
        new_pushups = current_pushups + input_pushups
        new_pullups = current_pullups + input_pullups
        new_dips = current_dips + input_dips
        new_total = new_pushups + new_pullups + new_dips
        
        # Zurückschreiben: Update Zellen B, C, D, E (Spalten 2-5)
        # gspread range update ist effizienter als einzelne cells
        ws_totals.update_cell(row_num, 2, new_total)   # Total
        ws_totals.update_cell(row_num, 3, new_pushups) # Pushups
        ws_totals.update_cell(row_num, 4, new_pullups) # Pullups
        ws_totals.update_cell(row_num, 5, new_dips)    # Dips
        
        # 2. Logs schreiben
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entries = []
        msg_parts = []
        
        if input_pushups > 0:
            log_entries.append([timestamp, name, input_pushups, "Pushups"])
            msg_parts.append(f"{input_pushups} Pushups")
        if input_pullups > 0:
            log_entries.append([timestamp, name, input_pullups, "Pullups"])
            msg_parts.append(f"{input_pullups} Pullups")
        if input_dips > 0:
            log_entries.append([timestamp, name, input_dips, "Dips"])
            msg_parts.append(f"{input_dips} Dips")
            
        if log_entries:
            ws_logs.append_rows(log_entries)
            
        summary_msg = " und ".join(msg_parts)
        return True, summary_msg
        
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False, ""

def save_full_edits(edited_logs_df):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        
        # 1. Logs überschreiben
        ws_logs = sheet.get_worksheet(1)
        ws_logs.clear()
        data_to_write = [edited_logs_df.columns.values.tolist()] + edited_logs_df.values.tolist()
        ws_logs.update(data_to_write)
        
        # 2. Totals neu berechnen
        edited_logs_df['Amount'] = pd.to_numeric(edited_logs_df['Amount'], errors='coerce').fillna(0)
        pivot_totals = edited_logs_df.groupby(['Name', 'Exercise'])['Amount'].sum().unstack(fill_value=0)
        
        all_names = ["Kevin", "Sämi", "Eric", "Elia"]
        
        final_data = []
        for name in all_names:
            # Zeilenstruktur: Name, Total, Pushups, Pullups, Dips
            row = {'Name': name}
            
            p_val = int(pivot_totals.loc[name, 'Pushups']) if (name in pivot_totals.index and 'Pushups' in pivot_totals.columns) else 0
            pu_val = int(pivot_totals.loc[name, 'Pullups']) if (name in pivot_totals.index and 'Pullups' in pivot_totals.columns) else 0
            d_val = int(pivot_totals.loc[name, 'Dips']) if (name in pivot_totals.index and 'Dips' in pivot_totals.columns) else 0
            
            total_val = p_val + pu_val + d_val
            
            row['Total'] = total_val
            row['Pushups'] = p_val
            row['Pullups'] = pu_val
            row['Dips'] = d_val
            
            final_data.append(row)
            
        final_df = pd.DataFrame(final_data)
        
        # 3. Totals schreiben (Spaltenreihenfolge beachten)
        final_df = final_df[['Name', 'Total', 'Pushups', 'Pullups', 'Dips']]
        
        ws_totals = sheet.get_worksheet(0)
        ws_totals.clear()
        totals_data = [final_df.columns.values.tolist()] + final_df.values.tolist()
        ws_totals.update(totals_data)
        
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern der Änderungen: {e}")
        return False

# --- RENDER FUNKTION ---
def render_track_html(current_df, display_date=None):
    if current_df.empty: return ""
    
    # Sortieren basierend auf dem aktuellen Score
    df_sorted = current_df.sort_values('Score', ascending=False)
    leader_name = df_sorted.iloc[0]['Name']
    last_place_name = df_sorted.iloc[-1]['Name']
    
    track_html = '<div class="racetrack">'
    
    # --- GRID ---
    total_segments = 12
    segment_width = 100.0 / total_segments
    
    for k in range(0, 11): 
        pos_percent = (k + 1) * segment_width
        label = f"{k}k"
        css_class = "grid-line-base grid-line"
        text_class = "grid-text"
        
        if k == 0:
            label = "Start"
            css_class = "grid-line-base start-line-marker"
            text_class = "grid-text grid-text-major"
        elif k == 5:
            css_class = "grid-line-base major-line" 
            text_class = "grid-text grid-text-major"
        elif k == 10:
            label = "Finish"
            css_class = "grid-line-base finish-line-marker"
            text_class = "grid-text grid-text-major"
            
        track_html += f"""
<div class="{css_class}" style="left: {pos_percent}%;">
<span class="{text_class}">{label}</span>
</div>
"""

    if display_date:
        track_html += f'<div class="date-display">📅 {display_date}</div>'
    
    all_names = ["Kevin", "Sämi", "Eric", "Elia"] 
    
    for i, name in enumerate(all_names):
        user_row = current_df[current_df['Name'] == name]
        raw_score = user_row.iloc[0]['Score'] if not user_row.empty else 0
        
        start_offset = segment_width
        playable_range = segment_width * 10 
        
        progress_ratio = min(1.0, raw_score / GOAL)
        final_pos_percent = start_offset + (progress_ratio * playable_range)
        
        if name == leader_name and raw_score > 0:
            current_icon = IMG_FIRST
        elif name == last_place_name and raw_score > 0:
            current_icon = IMG_LAST
        else:
            current_icon = IMG_MIDDLE
            
        top_divider_html = ""
        bottom_style = "dashed"
        bottom_color = "rgba(255,255,255,0.15)" 

        if i == 0:
            top_divider_html = '<div class="lane-divider" style="top: 0; border-bottom-style: solid; border-bottom-color: rgba(255,255,255,0.3);"></div>'
        if i == len(all_names) - 1:
            bottom_style = "solid"
            bottom_color = "rgba(255,255,255,0.3)" 

        track_html += f"""
<div class="lane">
{top_divider_html}
<div class="lane-divider" style="bottom: 0; border-bottom-style: {bottom_style}; border-bottom-color: {bottom_color};"></div>
<div class="horse-container" style="left: {final_pos_percent}%;">
<img src="{current_icon}" class="race-img">
<span class="name-tag">{name} ({int(raw_score)})</span>
</div>
</div>
"""
    track_html += '</div>'
    return track_html

# --- MAIN APP ---
st.title("🐎 Fitness Derby")

# --- FILTER UI ---
selected_filter = st.selectbox("Anzeige filtern:", ["Gesamt (Alle Punkte)", "Pushups", "Pullups", "Dips"])

# Platzhalter
share_placeholder = st.empty()
race_placeholder = st.empty()
skip_btn_placeholder = st.empty()

if 'has_animated' not in st.session_state:
    st.session_state.has_animated = False

# --- LOAD DATA ---
df_totals = get_data(0)
df_logs = get_data(1)

if df_totals.empty:
    st.warning("Warte auf Daten (oder DB Verbindung prüfen)...")
    st.stop()

# --- DATEN VORBEREITUNG (FILTER LOGIK) ---
# Wir berechnen für die Anzeige ein "Score" Feld basierend auf dem Filter
df_display = df_totals.copy()
for ex in EXERCISES:
    if ex not in df_display.columns:
        df_display[ex] = 0 

if selected_filter == "Gesamt (Alle Punkte)":
    # Wir nehmen die Total Spalte aus dem Sheet (oder summieren neu zur Sicherheit)
    if 'Total' in df_display.columns:
        df_display['Score'] = pd.to_numeric(df_display['Total'], errors='coerce').fillna(0)
    else:
        df_display['Score'] = df_display[EXERCISES].sum(axis=1)
else:
    # Nur die gewählte Spalte
    df_display['Score'] = df_display[selected_filter]

# --- SUCCESS & SHARE LOGIC ---
if 'last_log' in st.session_state:
    log_data = st.session_state.last_log
    
    # Leaderboard String für WhatsApp
    df_sorted_for_wa = df_display.sort_values('Score', ascending=False)
    leaderboard_text = ""
    rank = 1
    for _, row in df_sorted_for_wa.iterrows():
        leaderboard_text += f"{rank}. {row['Name']}: {int(row['Score'])}\n"
        rank += 1
    
    wa_text = f"🐎 *Update!*\n*{log_data['name']}* hat gerade *{log_data['msg']}* gemacht! 💪\n\n🏆 *Stand ({selected_filter}):*\n{leaderboard_text}\n🔗 https://pushupchallenge-zd5abepwkexdjtpsfbyzf6.streamlit.app/"
    wa_url = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"
    
    with share_placeholder.container():
        st.success(f"✅ {log_data['msg']} für {log_data['name']} gespeichert!")
        st.markdown(f"""
        <a href="{wa_url}" target="_blank" class="whatsapp-btn">
            📢 In WhatsApp-Gruppe teilen
        </a>
        """, unsafe_allow_html=True)
        st.write("")
    
    del st.session_state.last_log

# --- ANIMATION LOGIC ---
# Die Animation nutzt nun auch die gefilterten Logs
if not st.session_state.has_animated and not df_logs.empty:
    
    with skip_btn_placeholder:
        if st.button("⏩ Animation überspringen"):
            st.session_state.has_animated = True
            st.rerun()

    all_names = ["Kevin", "Sämi", "Eric", "Elia"]
    race_scores = {name: 0 for name in all_names}
    
    initial_df = pd.DataFrame([{'Name': n, 'Score': 0} for n in all_names])
    race_placeholder.markdown(render_track_html(initial_df, "Start"), unsafe_allow_html=True)
    time.sleep(0.5)
    
    if 'Timestamp' in df_logs.columns:
        df_logs['Timestamp'] = pd.to_datetime(df_logs['Timestamp'], errors='coerce')
        df_logs = df_logs.sort_values('Timestamp')
    
    if 'Amount' in df_logs.columns:
        df_logs['Amount'] = pd.to_numeric(df_logs['Amount'], errors='coerce').fillna(0)
        
        for index, row in df_logs.iterrows():
            if st.session_state.has_animated:
                break
                
            name = row['Name']
            amount = row['Amount']
            exercise = row.get('Exercise', 'Pushups')
            
            # Filter Logik für Animation
            points_to_add = 0
            if selected_filter == "Gesamt (Alle Punkte)":
                points_to_add = amount
            elif exercise == selected_filter:
                points_to_add = amount
            
            current_ts = row['Timestamp']
            date_str = current_ts.strftime('%d.%m.%Y') if pd.notnull(current_ts) else ""
            
            if points_to_add > 0:
                if name in race_scores:
                    race_scores[name] += points_to_add
                
                frame_data = [{'Name': n, 'Score': s} for n, s in race_scores.items()]
                frame_df = pd.DataFrame(frame_data)
                
                race_placeholder.markdown(render_track_html(frame_df, display_date=date_str), unsafe_allow_html=True)
                time.sleep(0.2) 

    st.session_state.has_animated = True
    
skip_btn_placeholder.empty()

# --- FINAL STATE ---
today_str = datetime.now().strftime('%d.%m.%Y')
race_placeholder.markdown(render_track_html(df_display, today_str), unsafe_allow_html=True)

# --- EINGABE FORMULAR (MULTI) ---
with st.form("log_form", clear_on_submit=True):
    names_list = ["Kevin", "Sämi", "Eric", "Elia"]
    who = st.selectbox("Wer bist du?", names_list)
    
    st.write("Was hast du gemacht?")
    c1, c2, c3 = st.columns(3)
    with c1:
        in_push = st.number_input("Pushups", min_value=0, value=0, step=1)
    with c2:
        in_pull = st.number_input("Pullups", min_value=0, value=0, step=1)
    with c3:
        in_dips = st.number_input("Dips", min_value=0, value=0, step=1)
    
    submitted = st.form_submit_button("🚀 Eintragen", use_container_width=True)

    if submitted:
        if in_push == 0 and in_pull == 0 and in_dips == 0:
            st.error("Bitte mindestens eine Übung eintragen.")
        else:
            with st.spinner("Speichere..."):
                success, msg = update_batch_entry(who, in_push, in_pull, in_dips)
                if success:
                    st.session_state.last_log = {'name': who, 'msg': msg}
                    st.rerun()

# --- STATS CALC ---
df_sorted = df_display.sort_values('Score', ascending=False)
leader = df_sorted.iloc[0]
remaining = GOAL - leader['Score']
total_team_reps = int(df_display['Score'].sum())

start_date = datetime.now()
days_passed = 1
if not df_logs.empty and 'Timestamp' in df_logs.columns:
    start_date = df_logs['Timestamp'].min()
    days_passed = (datetime.now() - start_date).days
    days_passed = max(1, days_passed)

col1, col2 = st.columns(2)

# LINKE KARTE: Leaderboard mit Breakdown
with col1:
    leaderboard_html = '<div class="metric-card">'
    leaderboard_html += f'<h3 style="margin:0; font-size:16px; color:#666; margin-bottom:15px;">🏆 Leaderboard ({selected_filter})</h3>'
    
    rank = 1
    for index, row in df_sorted.iterrows():
        name = row['Name']
        score = int(row['Score'])
        
        # Breakdown String (nur bei Gesamt interessant)
        detail_str = ""
        if selected_filter == "Gesamt (Alle Punkte)":
            parts = []
            for ex in EXERCISES:
                val = int(row.get(ex, 0))
                parts.append(f"{ex[:2].upper()}:{val}") # PU:100, DI:50
            detail_str = " | ".join(parts)
        
        # Prognose
        daily_avg = 0
        forecast_str = ""
        if score > 0:
            daily_avg = score / days_passed
            remaining_for_player = GOAL - score
            if remaining_for_player <= 0:
                forecast_str = "✅ Done"
            else:
                days_to_go = remaining_for_player / daily_avg
                finish_date = datetime.now() + timedelta(days=days_to_go)
                forecast_str = f"🏁 {finish_date.strftime('%d.%m.%y')}"

        leaderboard_html += f"""
<div class="leader-row">
<div style="display:flex; align-items:center;">
<span class="rank-badge">{rank}</span>
<div class="player-info">
<span class="player-name">{name}</span>
<span class="forecast-date">Ø {daily_avg:.1f}/Tag • {forecast_str}</span>
</div>
</div>
<div style="text-align:right;">
<span class="score-display">{score}</span>
<span class="score-detail">{detail_str}</span>
</div>
</div>
"""
        rank += 1
        
    leaderboard_html += '</div>'
    st.markdown(leaderboard_html, unsafe_allow_html=True)

# RECHTE KARTE: Stats für den Filter
with col2:
    st.markdown(f"""
<div class="metric-card" style="text-align:center;">
<h3 style="margin:0; font-size:16px; color:#666;">📊 Statistik ({selected_filter})</h3>
<div style="margin-top:20px;">
<p style="margin:0; color:#888; font-size:12px;">Aktueller Leader</p>
<h2 style="margin:5px 0; font-size:24px; color:#3e4a38;">{leader['Name']}</h2>
</div>
<div style="margin-top:15px;">
<p style="margin:0; color:#888; font-size:12px;">Team Gesamt</p>
<h2 style="margin:5px 0; font-size:24px; color:#1e88e5;">{total_team_reps}</h2>
<p style="margin:0; color:#888; font-size:10px;">Punkte Total</p>
</div>
<div style="margin-top:15px; border-top:1px solid #eee; padding-top:10px;">
<p style="margin:0; font-size:11px; color:#666;">Noch offen (Leader): <b>{int(remaining) if remaining > 0 else 0}</b></p>
<p style="margin:0; font-size:11px; color:#666;">Laufzeit: <b>{days_passed} Tage</b></p>
</div>
</div>
""", unsafe_allow_html=True)

# 4. ADMIN
st.divider()
with st.expander("📝 Protokoll bearbeiten / Fehler korrigieren"):
    st.warning("Hier werden ALLE Logs angezeigt. Spalte 'Exercise' ist wichtig.")
    
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
