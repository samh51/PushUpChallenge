import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL = 10000

# 🔴 FIX 1: The "Pure" URL (No /edit, no parameters)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1EYEj7wC8Rdo2gCDP4__PQwknmvX75Y9PRkoDKqA8AUM"

# 🖼️ IMAGE CONFIGURATION
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
    }
    .lane {
        border-bottom: 3px dashed #6b7c62;
        padding: 20px 0;
        position: relative;
        height: 140px;
    }
    .horse-container {
        position: absolute;
        top: 10px;
        transition: left 0.5s ease-in-out;
        z-index: 10;
        text-align: center;
        width: 120px;
        transform: translateX(-50%);
    }
    .race-img {
        width: 100px;
        height: 100px;
        object-fit: contain;
        filter: drop-shadow(0px 4px 4px rgba(0,0,0,0.5));
        background-color: transparent;
        border-radius: 10px; 
    }
    .name-tag {
        display: block;
        font-size: 16px;
        font-weight: bold;
        color: white;
        background: rgba(0,0,0,0.7);
        padding: 4px 10px;
        border-radius: 6px;
        margin-top: -5px;
        white-space: nowrap;
    }
    .finish-line {
        position: absolute;
        right: 0; top: 0; bottom: 0; width: 15px;
        background-image: repeating-linear-gradient(45deg, #000, #000 10px, #fff 10px, #fff 20px);
        opacity: 0.6;
        z-index: 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_index):
    """
    Load data by TAB INDEX (0 = First Tab, 1 = Second Tab)
    This avoids errors if the tab is named 'Sheet1' vs 'Tabellenblatt1'
    """
    try:
        # Use index (0 or 1) instead of string name
        df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_index, ttl=0)
        return df
    except Exception as e:
        st.error(f"❌ Error loading Tab #{worksheet_index}: {e}")
        return pd.DataFrame()

def update_data(name, new_reps):
    try:
        # 1. Update Totals (Tab 0)
        df_totals = get_data(0)
        if df_totals.empty: return False
        
        user_idx = df_totals[df_totals['Name'] == name].index[0]
        current_val = pd.to_numeric(df_totals.at[user_idx, 'Pushups'])
        df_totals.at[user_idx, 'Pushups'] = current_val + new_reps
        
        # Write back to Tab 0
        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df_totals)

        # 2. Update Logs (Tab 1)
        df_logs = get_data(1)
        new_entry = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name,
            "Amount": new_reps
        }])
        
        if df_logs.empty:
            df_updated_logs = new_entry
        else:
            df_updated_logs = pd.concat([df_logs, new_entry], ignore_index=True)
            
        # Write back to Tab 1
        conn.update(spreadsheet=SHEET_URL, worksheet=1, data=df_updated_logs)
        return True
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False

# --- RENDER FUNCTION ---
def render_track_html(current_df):
    if current_df.empty: return ""
    
    df_sorted = current_df.sort_values('Pushups', ascending=False)
    leader_name = df_sorted.iloc[0]['Name']
    last_place_name = df_sorted.iloc[-1]['Name']
    
    track_html = '<div class="racetrack">'
    
    # HARDCODED NAMES to prevent lanes from jumping around
    all_names = ["Kevin", "Sämi", "Eric", "Elia"] 
    
    for name in all_names:
        user_row = current_df[current_df['Name'] == name]
        
        if not user_row.empty:
            raw_score = user_row.iloc[0]['Pushups']
        else:
            raw_score = 0
            
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
# 🔴 FIX 2: Load by Index (0 = Totals, 1 = Logs)
df_totals = get_data(0)
df_logs = get_data(1)

if df_totals.empty:
    st.warning("Waiting for data... (If this persists, check secrets.toml)")
    st.stop()

# --- ANIMATION LOGIC ---
if not st.session_state.has_animated and not df_logs.empty:
    
    race_df = df_totals.copy()
    race_df['Pushups'] = 0
    
    race_placeholder.markdown(render_track_html(race_df), unsafe_allow_html=True)
    time.sleep(0.5)
    
    df_logs['Amount'] = pd.to_numeric(df_logs['Amount'], errors='coerce').fillna(0)
    
    total_steps = len(df_logs)
    step_size = max(1, int(total_steps / 25))
    
    for i in range(0, total_steps, step_size):
        current_slice = df_logs.iloc[:i+1]
        current_totals = current_slice.groupby('Name')['Amount'].sum().reset_index()
        current_totals.columns = ['Name', 'Pushups']
        
        frame_df = pd.merge(race_df[['Name']], current_totals, on='Name', how='left').fillna(0)
        
        race_placeholder.markdown(render_track_html(frame_df), unsafe_allow_html=True)
        time.sleep(0.03)

    st.session_state.has_animated = True

# --- FINAL STATE ---
race_placeholder.markdown(render_track_html(df_totals), unsafe_allow_html=True)

# 2. STATS
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

# 3. INPUT FORM
st.divider()
st.subheader("Log Your Reps")

with st.form("log_form", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    with col_a:
        # Check if Names column exists, if not use default list to prevent crash
        if 'Name' in df_totals.columns:
             names_list = df_totals['Name'].tolist()
        else:
             names_list = ["Kevin", "Sämi", "Eric", "Elia"]
             
        who = st.selectbox("Who are you?", names_list)
    with col_b:
        amount = st.number_input("Reps done:", min_value=1, value=20, step=1)
    
    submitted = st.form_submit_button("🚀 Update Score", use_container_width=True)

    if submitted:
        with st.spinner("Writing to database..."):
            success = update_data(who, amount)
            if success:
                st.success(f"Added {amount} pushups for {who}!")
                time.sleep(1)
                st.rerun()

st.caption("Data is live-synced with Google Sheets (Tab 1 & Tab 2).")
