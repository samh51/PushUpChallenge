import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION ---
GOAL = 10000
DATA_FILE = 'pushup_data.csv'
PLAYERS = ["Alex", "Sarah", "Mike", "Jessica"] # Change these to your names

# --- PAGE SETUP ---
st.set_page_config(page_title="Pushup Derby", page_icon="🐎", layout="centered")

# Custom CSS to make it look like a race track
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #f0f2f6;
    }
    .racetrack {
        background-color: #3e4a38;
        padding: 10px;
        border-radius: 10px;
        border-right: 5px solid #checkerboard; /* Placeholder */
        margin-bottom: 20px;
    }
    .lane {
        border-bottom: 2px dashed #6b7c62;
        padding: 10px 0;
        position: relative;
        height: 50px;
    }
    .horse-container {
        transition: left 0.5s ease-in-out;
        position: absolute;
        top: -10px;
        font-size: 30px;
        z-index: 10;
        white-space: nowrap;
    }
    .name-tag {
        font-size: 12px;
        color: white;
        background: rgba(0,0,0,0.5);
        padding: 2px 5px;
        border-radius: 4px;
        margin-left: -10px;
    }
    .finish-line {
        position: absolute;
        right: 0;
        top: 0;
        bottom: 0;
        width: 10px;
        background-image: repeating-linear-gradient(
            45deg,
            #000,
            #000 10px,
            #fff 10px,
            #fff 20px
        );
        opacity: 0.5;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA HANDLING ---
def load_data():
    if not os.path.exists(DATA_FILE):
        # Initialize with 0 if file doesn't exist
        df = pd.DataFrame({
            'Name': PLAYERS,
            'Pushups': [0] * len(PLAYERS)
        })
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

def update_data(name, count):
    df = load_data()
    # Add count to existing total
    df.loc[df['Name'] == name, 'Pushups'] += count
    df.to_csv(DATA_FILE, index=False)
    return df

# --- MAIN APP ---
st.title("🐎 10k Pushup Derby")

# Load current standings
df = load_data()

# 1. THE RACE TRACK VISUALIZATION
st.subheader("Current Standings")

# Sort by pushups (leader at top)
df_sorted = df.sort_values('Pushups', ascending=False)

track_html = '<div class="racetrack">'

for index, row in df.iterrows():
    # Calculate percentage (capped at 100%)
    progress = min(100, (row['Pushups'] / GOAL) * 100)
    
    # Create the HTML for this runner
    track_html += f"""
    <div class="lane">
        <div class="finish-line"></div>
        <div class="horse-container" style="left: {progress}%;">
            🐎 <span class="name-tag">{row['Name']} ({row['Pushups']})</span>
        </div>
    </div>
    """

track_html += '</div>'
st.markdown(track_html, unsafe_allow_html=True)


# 2. INPUT SECTION
st.divider()
st.subheader("Log Your Reps")

with st.form("log_form"):
    col1, col2 = st.columns(2)
    with col1:
        who = st.selectbox("Who are you?", PLAYERS)
    with col2:
        amount = st.number_input("How many pushups?", min_value=1, value=20, step=1)
    
    submitted = st.form_submit_button("Update Score", use_container_width=True)

    if submitted:
        update_data(who, amount)
        st.success(f"Added {amount} pushups for {who}!")
        st.rerun()

# 3. STATISTICS
st.divider()
st.caption(f"Goal: {GOAL} pushups")
leader = df_sorted.iloc[0]
remaining = GOAL - leader['Pushups']
if remaining > 0:
    st.caption(f"Leader needs {remaining} more to win!")
else:
    st.balloons()
    st.success(f"WINNER: {leader['Name']}!")
