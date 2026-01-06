import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL = 10000
SHEET_URL = "https://docs.google.com/spreadsheets/d/1EYEj7wC8Rdo2gCDP4__PQwknmvX75Y9PRkoDKqA8AUM/edit?gid=0#gid=0"

# 🖼️ IMAGE CONFIGURATION
IMG_FIRST  = "https://media.istockphoto.com/id/1007282190/vector/horse-power-flame.jpg?s=612x612&w=0&k=20&c=uHnnvMTzaatfPblbFHdfhuJT7qLwsARF90oqH0dMCjA="
IMG_MIDDLE = "https://t3.ftcdn.net/jpg/02/11/11/34/360_F_211113432_Gb89carZwwGuJA6lmux3NBU9tes3efMk.jpg"
IMG_LAST   = "https://i.etsystatic.com/28959621/r/il/e2cf08/5908874106/il_570xN.5908874106_80rl.jpg"

# --- PAGE SETUP ---
st.set_page_config(page_title="Pushup Derby", page_icon="🐎", layout="centered")

# Custom CSS (Sizes doubled)
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
        height: 140px; /* Doubled height */
    }
    .horse-container {
        position: absolute;
        top: 10px;
        transition: left 0.5s ease-in-out; /* Smoother transition for animation */
        z-index: 10;
        text-align: center;
        width: 120px; /* Doubled width */
        transform: translateX(-50%); /* Center the horse on the progress point */
    }
    .race-img {
        width: 100px; /* Doubled size */
        height: 100px; /* Doubled size */
        object-fit: contain;
        filter: drop-shadow(0px 4px 4px rgba(0,0,0,0.5));
        background-color: transparent;
        border-radius: 10px; 
    }
    .name-tag {
        display: block;
        font-size: 16px; /* Larger text */
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

def get_data(worksheet_name):
    try:
        # We specify worksheet to grab either 'Sheet1' (Totals) or 'Logs'
        df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        return df
    except Exception as e:
        return pd.DataFrame()

def update_data(name, new_reps):
    try:
        # 1. Update Totals (Sheet1) - For quick access
        df_totals = get_data("Sheet1") # Assuming default tab is Sheet1
        if df_totals.empty: return False
        
        user_idx = df_totals[df_totals['Name'] == name].index[0]
        df_totals.at[user_idx, 'Pushups'] = pd.to_numeric(df_totals.at[user_idx, 'Pushups']) + new_reps
        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=df_totals)

        # 2. Update Logs (Logs) - For history/animation
        # We read existing logs, append new row, and write back
        df_logs = get_data("Logs")
        new_entry = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name,
            "Amount": new_reps
        }])
        
        if df_logs.empty:
            df_updated_logs = new_entry
        else:
            df_updated_logs = pd.concat([df_logs, new_entry], ignore_index=True)
            
        conn.update(spreadsheet=SHEET_URL, worksheet="Logs", data=df_updated_logs)
        return True
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False

# --- RENDER FUNCTION (Generates the HTML) ---
def render_track_html(current_df):
    if current_df.empty: return ""
    
    # Sort to find leader/last place for THIS specific frame
    df_sorted = current_df.sort_values('Pushups', ascending=False)
    leader_name = df_sorted.iloc[0]['Name']
    last_place_name = df_sorted.iloc[-1]['Name']
    
    track_html = '<div class="racetrack">'
    
    # We iterate through the original list of names to keep lane order consistent
    # (So horses don't swap lanes, they just move forward/backward)
    all_names = ["Kevin", "Sämi", "Eric", "Elia"] # HARDCODED ORDER for stability or get from initial df
    
    for name in all_names:
        # Find user data in the current dataframe
        user_row = current_df[current_df['Name'] == name]
        
        if not user_row.empty:
            raw_score = user_row.iloc[0]['Pushups']
        else:
            raw_score = 0
            
        progress = min(90, (raw_score / GOAL) * 100)
        
        # Icon Logic
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

# Placeholder for the race track
race_placeholder = st.empty()

# Initialize Session State for Animation
if 'has_animated' not in st.session_state:
    st.session_state.has_animated = False

# --- LOAD DATA ---
df_totals = get_data("Sheet1")
df_logs = get_data("Logs")

if df_totals.empty:
    st.error("Could not load data. Ensure Sheet1 exists.")
    st.stop()

# --- ANIMATION LOGIC ---
# Only animate if we haven't done it yet this session AND we have logs
if not st.session_state.has_animated and not df_logs.empty:
    
    # 1. Setup the "Race" dataframe (everyone starts at 0)
    # Get unique names from Totals to ensure we have everyone
    race_df = df_totals.copy()
    race_df['Pushups'] = 0
    
    # 2. Show Starting Line
    race_placeholder.markdown(render_track_html(race_df), unsafe_allow_html=True)
    time.sleep(0.5)
    
    # 3. Process logs to create animation steps
    # We group logs by small chunks or simply iterate if not too many
    # For speed, let's replay by accumulating log entries
    
    # Clean logs
    df_logs['Amount'] = pd.to_numeric(df_logs['Amount'], errors='coerce').fillna(0)
    
    # Replay Loop
    total_steps = len(df_logs)
    # If too many logs, skip frames to keep animation under 3 seconds
    step_size = max(1, int(total_steps / 20)) 
    
    for i in range(0, total_steps, step_size):
        # Get the slice of logs up to this point
        current_slice = df_logs.iloc[:i+1]
        
        # Calculate totals for this slice
        current_totals = current_slice.groupby('Name')['Amount'].sum().reset_index()
        current_totals.columns = ['Name', 'Pushups']
        
        # Merge with base frame to ensure all players exist (even if 0 pushups)
        frame_df = pd.merge(race_df[['Name']], current_totals, on='Name', how='left').fillna(0)
        
        # Update UI
        race_placeholder.markdown(render_track_html(frame_df), unsafe_allow_html=True)
        time.sleep(0.05) # Speed of animation

    # Mark animation as done
    st.session_state.has_animated = True

# --- FINAL STATE RENDER ---
# Ensure the final accurate data is shown after animation (or if no logs exist)
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
        who = st.selectbox("Who are you?", df_totals['Name'].tolist())
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

st.caption("Data is live-synced with Google Sheets (Totals & Logs).")
