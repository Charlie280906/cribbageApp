import streamlit as st
import sqlite3
import random
import json

st.set_page_config(page_title="Cribbage Tracker", layout="centered")

# =====================================================
# DATABASE SETUP
# =====================================================

DB_FILE = "cribbage.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_game_db(game):
    conn = get_conn()
    c = conn.cursor()
    data = json.dumps(game)
    c.execute("DELETE FROM game_state")  # overwrite previous
    c.execute("INSERT INTO game_state (data) VALUES (?)", (data,))
    conn.commit()
    conn.close()

def load_game_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT data FROM game_state LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def clear_game_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM game_state")
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# =====================================================
# INITIAL LOAD
# =====================================================
if "game" not in st.session_state:
    st.session_state.game = load_game_db()

if "page" not in st.session_state:
    st.session_state.page = "landing" if not st.session_state.game else "game"

# =====================================================
# RULES PAGE
# =====================================================
def rules_page():
    st.title("How to Play Cribbage")
    st.markdown("""
### Pegging Points
- 15 = 2  
- 31 = 2  
- Pair = 2  
- Triple = 6  
- 3 in a Row = 6  
- Starting Jack = 2 (dealer)  
- Couldn't Play = 1  

Dealer rotates each round.  
First to 121 wins.
""")
    if st.button("⬅ Back"):
        st.session_state.page = "game" if st.session_state.game else "landing"
        st.rerun()

# =====================================================
# LANDING PAGE
# =====================================================
def landing_page():
    st.title("🃏 Cribbage Score Tracker")
    num_players = st.number_input("Number of Players", min_value=2, step=1)
    st.divider()

    names = []
    for i in range(num_players):
        names.append(st.text_input(f"Player {i+1} Name", key=f"name_{i}").title())

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Game", use_container_width=True, type="primary", icon="🏁"):
            if all(names):
                dealer_index = random.randint(0, num_players - 1)
                game = {
                    "players": names,
                    "scores": [0] * num_players,
                    "dealer_index": dealer_index,
                    "round": 1
                }
                st.session_state.game = game
                save_game_db(game)
                st.session_state.page = "game"
                st.rerun()
            else:
                st.error("Please enter all player names.")

    with col2:
        if st.button("How to Play", use_container_width=True, icon="❓"):
            st.session_state.page = "rules"
            st.rerun()

# =====================================================
# GAME PAGE
# =====================================================
def game_page():
    game = st.session_state.game

    def update_and_save():
        st.session_state.game = game
        save_game_db(game)
        st.rerun()

    st.title("🃏 Cribbage Tracker")
    st.markdown(f"### Round {game['round']}")

    # DEALER CONTROLS
    with st.container():
        dealer_name = game["players"][game["dealer_index"]]
        st.markdown(f"#### Current Dealer: **{dealer_name}**")

        if st.button("New Round", use_container_width=True, type="primary"):
            game["dealer_index"] = (game["dealer_index"] + 1) % len(game["players"])
            game["round"] += 1
            update_and_save()

        if st.button("Split to Jack", use_container_width=True):
            game["scores"][game["dealer_index"]] += 2
            update_and_save()

    st.divider()

    # PLAYER CONTAINERS
    for i, player in enumerate(game["players"]):
        with st.container():
            col1, col2 = st.columns(2)
            col1.subheader(player)
            col2.markdown(f"#### Score: {game['scores'][i]}")

            row1 = st.columns(3)
            row2 = st.columns(3)

            # Row 1 buttons
            if row1[0].button("Made 15", key=f"15_{i}", use_container_width=True):
                game["scores"][i] += 2
                update_and_save()
            if row1[1].button("Made 31", key=f"31_{i}", use_container_width=True):
                game["scores"][i] += 2
                update_and_save()
            if row1[2].button("Pair", key=f"pair_{i}", use_container_width=True):
                game["scores"][i] += 2
                update_and_save()

            # Row 2 buttons
            if row2[0].button("Triple", key=f"triple_{i}", use_container_width=True):
                game["scores"][i] += 6
                update_and_save()
            if row2[1].button("3 in a Row", key=f"run_{i}", use_container_width=True):
                game["scores"][i] += 6
                update_and_save()
            if row2[2].button("Prev. Couldn't Play", key=f"go_{i}", use_container_width=True):
                game["scores"][i] += 1
                update_and_save()

    st.divider()

    # TOP CONTROLS
    col1, col2 = st.columns(2)
    with col2:
        if st.button("How to Play", use_container_width=True, icon="❓"):
            st.session_state.page = "rules"
            st.rerun()
    with col1:
        if st.button("Reset Game", use_container_width=True, type="primary", icon="🗑️"):
            clear_game_db()
            st.session_state.game = None
            st.session_state.page = "landing"
            st.rerun()

# =====================================================
# ROUTING
# =====================================================
if st.session_state.page == "rules":
    rules_page()
elif st.session_state.page == "landing":
    landing_page()
else:
    game_page()