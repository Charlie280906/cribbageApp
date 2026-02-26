import streamlit as st
import sqlite3
import random
import json
from datetime import datetime

st.set_page_config(page_title="Cribbage Tracker", layout="centered")

DB_FILE = "cribbage.db"

# =====================================================
# DATABASE
# =====================================================

def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS active_games (
            pin TEXT PRIMARY KEY,
            data TEXT,
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            player TEXT PRIMARY KEY,
            total_points INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()

# =====================================================
# GAME DB
# =====================================================

def save_game(pin, game):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "REPLACE INTO active_games (pin, data, updated_at) VALUES (?, ?, ?)",
        (pin, json.dumps(game), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def load_game(pin):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT data FROM active_games WHERE pin=?", (pin,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def delete_game(pin):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM active_games WHERE pin=?", (pin,))
    conn.commit()
    conn.close()

def pin_exists(pin):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM active_games WHERE pin=?", (pin,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# =====================================================
# LEADERBOARD
# =====================================================

def update_leaderboard(game):
    conn = get_conn()
    c = conn.cursor()

    for player, score in zip(game["players"], game["scores"]):
        c.execute("SELECT total_points FROM leaderboard WHERE player=?", (player,))
        row = c.fetchone()

        if row:
            c.execute("UPDATE leaderboard SET total_points=? WHERE player=?",
                      (row[0] + score, player))
        else:
            c.execute("INSERT INTO leaderboard (player, total_points) VALUES (?, ?)",
                      (player, score))

    conn.commit()
    conn.close()

def get_leaderboard():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT player, total_points FROM leaderboard ORDER BY total_points DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# =====================================================
# SESSION INIT
# =====================================================

if "page" not in st.session_state:
    st.session_state.page = "pin"

if "current_pin" not in st.session_state:
    st.session_state.current_pin = None

if "game" not in st.session_state:
    st.session_state.game = None

# =====================================================
# PIN SCREEN
# =====================================================

def pin_screen():
    st.title("🃏 Cribbage Tracker")

    pin = st.text_input("Enter 4 Digit PIN", max_chars=4)

    if st.button("Join Game", width="stretch", type="primary", icon="✅"):
        if len(pin) == 4 and pin.isdigit():
            game = load_game(pin)
            if game:
                st.session_state.current_pin = pin
                st.session_state.game = game
                st.session_state.page = "game"
                st.rerun()
            else:
                st.error("No game found with that PIN.")
        else:
            st.error("PIN must be 4 digits.")

    st.divider()

    if st.button("Create New Game", icon="✏️", width="stretch"):
        st.session_state.page = "create"
        st.rerun()

# =====================================================
# CREATE GAME
# =====================================================

def create_game_screen():
    st.title("🃏 Cribbage Tracker")

    num_players = st.number_input("Number of Players", min_value=2, step=1)

    st.divider()

    pin = st.text_input("Create 4 Digit Game PIN", max_chars=4)

    st.divider()

    names = []
    for i in range(num_players):
        names.append(st.text_input(f"Player {i+1} Name", key=f"name_create_{i}").title())

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Game", type="primary", width="stretch", icon="🏁"):
            if not (len(pin) == 4 and pin.isdigit()):
                st.error("PIN must be exactly 4 digits.")
                return

            if pin_exists(pin):
                st.error("PIN already in use.")
                return

            if not all(names):
                st.error("Enter all player names.")
                return

            game = {
                "players": names,
                "scores": [0] * num_players,
                "dealer_index": random.randint(0, num_players - 1),
                "round": 1,
                "history": []
            }

            save_game(pin, game)

            st.session_state.current_pin = pin
            st.session_state.game = game
            st.session_state.page = "game"
            st.rerun()

    with col2:
        if st.button("Back", width="stretch", icon="↩️"):
            st.session_state.page = "pin"
            st.rerun()

# =====================================================
# UNDO DIALOG
# =====================================================

@st.dialog("Confirm Undo")
def confirm_undo():
    if st.button("Yes, Undo", width="stretch", icon="⚠️"):
        game = st.session_state.game
        if game["history"]:
            previous_state = game["history"].pop()
            st.session_state.game = previous_state
            save_game(st.session_state.current_pin, previous_state)
        st.rerun()

# =====================================================
# GAME SCREEN
# =====================================================

def game_screen():
    game = st.session_state.game
    pin = st.session_state.current_pin

    def record_history():
        snapshot = json.loads(json.dumps(game))
        game["history"].append(snapshot)

    def apply_and_save():
        st.session_state.game = game
        save_game(pin, game)
        st.rerun()

    st.title("🃏 Cribbage Tracker")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### Round {game['round']}")

    with col2:
        st.markdown(f"### Game PIN: {pin}")

    with st.container(border=True):
        dealer = game["players"][game["dealer_index"]]
        st.markdown(f"#### Dealer: **{dealer}**")

        if st.button("New Round", width="stretch", type="primary"):
            record_history()
            game["dealer_index"] = (game["dealer_index"] + 1) % len(game["players"])
            game["round"] += 1
            apply_and_save()

        if st.button("Split to Jack", width="stretch"):
            record_history()
            game["scores"][game["dealer_index"]] += 2
            apply_and_save()

    st.divider()

    for i, player in enumerate(game["players"]):
        with st.container(border=True):
            col1, col2 = st.columns(2)
            col1.subheader(player)
            col2.markdown(f"### {game['scores'][i]}")

            def add_score(points):
                record_history()
                game["scores"][i] += points
                apply_and_save()

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Made 15", key=f"15_{i}", width="stretch"):
                    add_score(2)

            with col2:
                if st.button("Made 31", key=f"31_{i}", width="stretch"):
                    add_score(2)

            with col3:
                if st.button("Pair", key=f"pair_{i}", width="stretch"):
                    add_score(2)

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Triple", key=f"triple_{i}", width="stretch"):
                    add_score(6)

            with col2:
                if st.button("3 in a Row", key=f"run_{i}", width="stretch"):
                    add_score(6)

            with col3:
                if st.button("Prev. Couldn't Play", key=f"go_{i}", width="stretch"):
                    add_score(1)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Finish Game", type="primary", width="stretch", icon="🛑"):
            update_leaderboard(game)
            delete_game(pin)
            st.session_state.page = "leaderboard"
            st.session_state.game = None
            st.rerun()

    with col2:
        if st.button("Undo", width="stretch", icon="🔄"):
            confirm_undo()

    if st.button("Exit to PIN", width="stretch", icon="🗑️"):
        st.session_state.page = "pin"
        st.session_state.game = None
        st.session_state.current_pin = None
        st.rerun()

# =====================================================
# LEADERBOARD SCREEN
# =====================================================

def leaderboard_screen():
    st.title("🏆 Cribbage All-Time Leaderboard")

    rows = get_leaderboard()

    if not rows:
        st.info("No games recorded yet.")
        return

    table_data = []
    for idx, (player, score) in enumerate(rows, start=2):
        table_data.append({
            "Position": idx,
            "Player": player,
            "Overall Score": score
        })

    st.table(table_data)

    st.divider()

    col1, col2 = st.columns(2)

    with col2:
        if st.button("Join Game with PIN", width="stretch", icon="🔑"):
            st.session_state.page = "pin"
            st.rerun()

    with col1:
        if st.button("Start New Game", width="stretch", icon="✏️", type="primary"):
            st.session_state.page = "create"
            st.rerun()

# =====================================================
# ROUTING
# =====================================================

if st.session_state.page == "pin":
    pin_screen()
elif st.session_state.page == "create":
    create_game_screen()
elif st.session_state.page == "game":
    game_screen()
else:
    leaderboard_screen()