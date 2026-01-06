import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL = 10000

# --- PAGE SETUP ---
st.set_page_config(page_title="Pushup Derby", page_icon="🐎", layout="centered")

# Custom CSS for the Race Track
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
        height: 60px;
    }
    .horse-container {
        position: absolute;
        top: -5px;
        font-size: 30px;
        white-space: nowrap;
        transition: left 1s ease-in-out;
        z-index: 10;
    }
    .name-tag {
        font-size: 14px;
        font-weight: bold;
        color: white;
        background: rgba(0,0,0,0.6);
        padding: 4px 8px;
        border-radius: 6px;
        margin-left: -5px;
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
# This automatically finds the credentials in your secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # ttl=0 ensures we don't cache old data
    try:
        df = conn.read(ttl=0)
        # Ensure column types are correct
        if not df.empty:
            df['Pushups'] = pd.to_numeric(df['Pushups'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error reading sheet. Check your secrets.toml! Error: {e}")
        return pd.DataFrame()

def update_data(df, name, new_reps):
    # Find the row for the selected user
    user_idx = df[df['Name'] == name].index[0]
    
    # Update the local dataframe
    df.at[user_idx, 'Pushups'] += new_reps
    
    # Write the ENTIRE updated dataframe back to Google Sheets
    conn.update(data=df)
    return df

# --- MAIN APP ---
st.title("🐎 10k Pushup Derby")

# Load Data
df = get_data()

if df.empty:
    st.warning("Your Google Sheet appears to be empty or unreadable.")
    st.info("Make sure your Sheet has two columns in the first row: 'Name' and 'Pushups'.")
    st.stop()

# 1. THE RACE TRACK VISUALIZATION
st.subheader("Current Standings")

# Sort by score for the leaderboard logic
df_sorted = df.sort_values('Pushups', ascending=False)

track_html = '<div class="racetrack">'

for index, row in df.iterrows(): # We iterate original df to keep order consistent or use df_sorted for rank order
    # Calculate percentage (capped at 90% so the horse emoji doesn't disappear off-screen)
    raw_score = row['Pushups']
    progress = min(90, (raw_score / GOAL) * 100)
    
    track_html += f"""
    <div class="lane">
        <div class="finish-line"></div>
        <div class="horse-container" style="left: {progress}%;">
            🐎 <span class="name-tag">{row['Name']} ({int(raw_score)})</span>
        </div>
    </div>
    """

track_html += '</div>'
st.markdown(track_html, unsafe_allow_html=True)

# 2. STATS & LEADERBOARD
leader = df_sorted.iloc[0]
remaining = GOAL - leader['Pushups']

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🏆 Leader</h3>
        <h2>{leader['Name']}</h2>
        <p>{int(leader['Pushups'])} reps</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🏁 To Win</h3>
        <h2>{int(remaining) if remaining > 0 else 0}</h2>
        <p>reps needed</p>
    </div>
    """, unsafe_allow_html=True)

if remaining <= 0:
    st.balloons()
    st.success(f"🎉 RACE OVER! {leader['Name']} HAS WON!")

# 3. INPUT FORM
st.divider()
st.subheader("Log Your Reps")

with st.form("log_form", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    
    # Dropdown populated dynamically from the Google Sheet names
    with col_a:
        who = st.selectbox("Who are you?", df['Name'].tolist())
    
    # Number input
    with col_b:
        amount = st.number_input("Reps done:", min_value=1, value=20, step=1)
    
    submitted = st.form_submit_button("🚀 Update Score", use_container_width=True)

    if submitted:
        with st.spinner("Updating the big board..."):
            update_data(df, who, amount)
        st.success(f"Added {amount} pushups for {who}!")
        st.rerun()

# Footer
st.caption("Data is live-synced with Google Sheets.")
