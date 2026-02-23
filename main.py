from itertools import count

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import json

from validators import length

# =====================================================
# JS READY — one-time rerun so JS components mount
# =====================================================
if "js_ready" not in st.session_state:
    st.session_state.js_ready = True
    st.rerun()


# =====================================================
# LOCAL STORAGE WRAPPER
# =====================================================

def ls_write(key: str, value):
    """Write Python object to browser localStorage safely"""
    json_value = json.dumps(value)
    streamlit_js_eval(
        js_expressions=f'localStorage.setItem("{key}", `{json_value}`);',
        key=f"ls_save_{key}"
    )



def ls_read(key: str):
    val = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{key}')",
        key=f"ls_load_{key}"
    )
    if val is None:
        return None
    try:
        return json.loads(val)
    except:
        return None



def ls_delete(key: str):
    streamlit_js_eval(
        js_expressions=f"localStorage.removeItem('{key}')",
        key=f"ls_del_{key}"
    )


# =====================================================
# CRIBBAGE GAME STATE SCHEMA
# =====================================================

def new_game_state(player_names):
    return {
        "players": player_names,
        "scores": [0] * len(player_names),
        "dealer": 0,
        "turn": 0,
        "phase": "setup",  # setup / deal / pegging / count
        "hands": {},
        "crib": [],
        "starter_card": None,
        "pegging_count": 0,
        "pegging_pile": [],
        "history": []
    }


# =====================================================
# STATE MANAGER
# =====================================================

GAME_KEY = "cribbage_game_state"


def load_game():
    state = ls_read(GAME_KEY)
    if state:
        st.session_state.game = state
    else:
        st.session_state.game = None


def save_game():
    if "game" in st.session_state and st.session_state.game:
        ls_write(GAME_KEY, st.session_state.game)


def update_game(updates: dict):
    st.session_state.game.update(updates)
    save_game()


# =====================================================
# INITIAL LOAD (once)
# =====================================================

if "game_load_phase" not in st.session_state:
    st.session_state.game_load_phase = 0

if st.session_state.game_load_phase == 0:
    # trigger JS read
    st.session_state._raw_game_json = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{GAME_KEY}')",
        key="init_ls_read"
    )
    st.session_state.game_load_phase = 1
    st.rerun()

elif st.session_state.game_load_phase == 1:
    raw = st.session_state._raw_game_json

    if raw:
        try:
            st.session_state.game = json.loads(raw)
        except:
            st.session_state.game = None
    else:
        st.session_state.game = None

    st.session_state.game_load_phase = 2


# =====================================================
# UI — TITLE
# =====================================================

st.title("Cribbage App")


# =====================================================
# SETUP SCREEN (only if no game exists)
# =====================================================

if not st.session_state.game:

    st.header("New Game Setup")

    num_players = st.number_input(
        "Number of players",
        min_value=2,
        max_value=4,
        value=2
    )

    st.divider()

    names = []
    for i in range(num_players):
        names.append(
            st.text_input(f"Player {i+1} name", key=f"name_{i}")
        )

    st.divider()

    if st.button("Start Game", type="primary"):

        if all(names):
            st.session_state.game = new_game_state(names)
            save_game()
            st.rerun()
        else:
            st.error("Enter all player names")


# =====================================================
# GAME SCREEN
# =====================================================

else:

    game = st.session_state.game

    st.subheader("Current Game")

    st.write("Players:", game["players"])
    st.write("Scores:", game["scores"])
    st.write("Dealer:", game["players"][game["dealer"]])
    st.write("Turn:", game["players"][game["turn"]])
    st.write("Phase:", game["phase"])


    # print(game["players"])
    # print(type(game["players"]))
    # print(len(game["players"]))


    for i in range(0, len(game["players"])):
        container = st.container(border=True)
        container.subheader(game["players"][i])



    st.divider()

    # -------------------------
    # Score buttons (demo)
    # -------------------------
    st.subheader("Add Points")

    for i, name in enumerate(game["players"]):
        if st.button(f"+2 for {name}", key=f"score_{i}"):
            game["scores"][i] += 2
            save_game()
            st.rerun()

    # -------------------------
    # Next turn
    # -------------------------
    if st.button("Next Turn"):
        game["turn"] = (game["turn"] + 1) % len(game["players"])
        save_game()
        st.rerun()

    # -------------------------
    # Rotate dealer
    # -------------------------
    if st.button("Rotate Dealer"):
        game["dealer"] = (game["dealer"] + 1) % len(game["players"])
        save_game()
        st.rerun()

    st.divider()

    # -------------------------
    # Reset game
    # -------------------------
    if st.button("Reset Game"):
        ls_delete(GAME_KEY)
        st.session_state.game = None
        st.rerun()


# =====================================================
# DEBUG PANEL
# =====================================================

with st.expander("Debug — Raw Stored JSON"):
    st.json(ls_read(GAME_KEY))
