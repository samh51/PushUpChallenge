import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL = 10000
SHEET_URL = "https://docs.google.com/spreadsheets/d/1EYEj7wC8Rdo2gCDP4__PQwknmvX75Y9PRkoDKqA8AUM/edit?gid=0#gid=0"

# 🖼️ IMAGE CONFIGURATION (Replace these with direct image links if needed)
# Note: These must be direct links to images (ending in .png, .jpg, .gif)
IMG_FIRST  = "https://media.istockphoto.com/id/1007282190/vector/horse-power-flame.jpg?s=612x612&w=0&k=20&c=uHnnvMTzaatfPblbFHdfhuJT7qLwsARF90oqH0dMCjA=" # Fire/Fast Horse placeholder
IMG_MIDDLE = "https://t3.ftcdn.net/jpg/02/11/11/34/360_F_211113432_Gb89carZwwGuJA6lmux3NBU9tes3efMk.jpg" # Running Horse placeholder
IMG_LAST   = "https://i.etsystatic.com/28959621/r/il/e2cf08/5908874106/il_570xN.5908874106_80rl.jpg" # Donkey placeholder

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
        border-bottom: 2px dashed #6b7c62;
        padding: 15px 0;
        position: relative;
        height: 70px; /* Increased height for images */
    }
    .horse-container {
        position: absolute;
        top: -10px;
        transition: left 1s ease-in-out;
        z-index: 10;
        text-align: center;
        width: 60px; /* Container width */
    }
    /* NEW: Style for the Race Icons */
    .race-img {
        width: 50px;
        height: 50px;
        object-fit: contain;
        filter: drop-shadow(0px 2px 2px rgba(0,0,0,0.5));
    }
    .name-tag {
        display: block; /* Force name below image */
        font-size: 11px;
        font-weight: bold;
        color: white;
        background: rgba(0,0,0,0.6);
        padding: 2px 6px;
        border-radius: 4px;
        margin-top: -5px;
        white-space: nowrap;
    }
    .finish-line {
        position: absolute;
        right: 0; top: 0; bottom: 0; width: 10px;
        background-image: repeating-linear-gradient(45deg, #000, #000 10px, #fff 10px, #fff 20px);
        opacity: 0.6;
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

def get_data():
    try:
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        if not df.empty:
            df['Pushups'] = pd.to_numeric(df['Pushups'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error reading sheet: {e}")
        return pd.DataFrame()

def update_data(df, name, new_reps):
    try:
        user_idx = df[df['Name'] == name].index[0]
        df.at[user_idx, 'Pushups'] += new_reps
        conn.update(spreadsheet=SHEET_URL, data=df)
        return df
    except Exception as e:
        st.error(f"Error updating data: {e}")
        return df

# --- MAIN APP ---
st.title("🐎 10k Pushup Derby")

df = get_data()

if df.empty:
    st.warning("Could not read data.")
    st.stop()

# 1. THE RACE TRACK VISUALIZATION
st.subheader("Current Standings")

# Calculate Ranks
df_sorted = df.sort_values('Pushups', ascending=False)
leader_name = df_sorted.iloc[0]['Name']
last_place_name = df_sorted.iloc[-1]['Name']

# Start the container
track_html = '<div class="racetrack">'

for index, row in df.iterrows(): 
    raw_score = row['Pushups']
    progress = min(90, (raw_score / GOAL) * 100)
    name = row['Name']
    
    # --- ICON LOGIC ---
    if name == leader_name:
        current_icon = IMG_FIRST
    elif name == last_place_name:
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
st.markdown(track_html, unsafe_allow_html=True)

# 2. STATS
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
        who = st.selectbox("Who are you?", df['Name'].tolist())
    with col_b:
        amount = st.number_input("Reps done:", min_value=1, value=20, step=1)
    
    submitted = st.form_submit_button("🚀 Update Score", use_container_width=True)

    if submitted:
        with st.spinner("Updating..."):
            update_data(df, who, amount)
        st.success(f"Added {amount} pushups for {who}!")
        st.rerun()
