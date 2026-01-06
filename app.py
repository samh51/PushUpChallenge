import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GOAL = 10000
# REPACE THIS WITH YOUR GOOGLE SHEET LINK
url = "https://docs.google.com/spreadsheets/d/1xB..........YOUR_LINK_HERE........./edit?usp=sharing"

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
    }
    .lane {
        border-bottom: 2px dashed #6b7c62;
        padding: 10px 0;
        position: relative;
        height: 50px;
    }
    .horse-container {
        position: absolute;
        top: -10px;
        font-size: 30px;
        white-space: nowrap;
        transition: left 1s ease-in-out;
    }
    .name-tag {
        font-size: 12px;
        color: white;
        background: rgba(0,0,0,0.5);
        padding: 2px 5px;
        border-radius: 4px;
    }
    .finish-line {
        position: absolute;
        right: 0; top: 0; bottom: 0; width: 10px;
        background-image: repeating-linear-gradient(45deg, #000, #000 10px, #fff 10px, #fff 20px);
        opacity: 0.5;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA HANDLING (GOOGLE SHEETS) ---
# Create a connection object
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # Read data from the Google Sheet
    # ttl=0 ensures we don't cache data, so we see updates instantly
    return conn.read(spreadsheet=url, usecols=[0, 1], ttl=0)

def update_score(name, reps):
    df = get_data()
    
    # Calculate new total
    current_score = df.loc[df['Name'] == name, 'Pushups'].values[0]
    new_total = current_score + reps
    
    # Update dataframe locally
    df.loc[df['Name'] == name, 'Pushups'] = new_total
    
    # Write back to Google Sheet
    conn.update(spreadsheet=url, data=df)
    return df

# --- MAIN APP ---
st.title("🐎 10k Pushup Derby")

try:
    df = get_data()
    
    # 1. THE RACE TRACK
    st.subheader("Current Standings")
    df_sorted = df.sort_values('Pushups', ascending=False)

    track_html = '<div class="racetrack">'
    for index, row in df.iterrows():
        # Calculate progress %
        progress = min(90, (row['Pushups'] / GOAL) * 100) # Cap at 90% so horse doesn't fly off screen
        
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
        # Get names dynamically from the sheet
        names_list = df['Name'].tolist()
        
        with col1:
            who = st.selectbox("Who are you?", names_list)
        with col2:
            amount = st.number_input("Reps done:", min_value=1, value=20, step=1)
        
        submitted = st.form_submit_button("Update Score", use_container_width=True)

        if submitted:
            update_score(who, amount)
            st.success(f"Added {amount} for {who}!")
            st.rerun()

    # 3. STATS
    st.divider()
    leader = df_sorted.iloc[0]
    st.caption(f"Leader: {leader['Name']} is {(leader['Pushups']/GOAL)*100:.1f}% of the way there!")

except Exception as e:
    st.error("Could not connect to Google Sheet. Make sure the link is correct and set to 'Anyone with link can Edit'.")
    st.error(e)
