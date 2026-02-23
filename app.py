import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import json
import random

st.set_page_config(page_title="Cribbage Tracker", layout="centered")

# =====================================================
# LOCAL STORAGE (NO DUPLICATE KEY ISSUE)
# =====================================================

def load_game():
    data = streamlit_js_eval(
        js_expressions="localStorage.getItem('cribbage_game')",
        key="load_game_once"
    )
    if data:
        return json.loads(data)
    return None


def save_game(data):
    streamlit_js_eval(
        js_expressions=f"localStorage.setItem('cribbage_game', `{json.dumps(data)}`)",
        key="save_game_once"
    )


def clear_game():
    streamlit_js_eval(
        js_expressions="localStorage.removeItem('cribbage_game')",
        key="clear_game_once"
    )


# =====================================================
# LOAD STATE
# =====================================================

if "game" not in st.session_state:
    st.session_state.game = load_game()

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

    if st.button("How to Play"):
        st.session_state.page = "rules"
        st.rerun()

    num_players = st.number_input("Number of Players", min_value=2, step=1)

    names = []
    for i in range(num_players):
        names.append(st.text_input(f"Player {i+1} Name", key=f"name_{i}"))

    if st.button("Start Game"):
        if all(names):
            dealer_index = random.randint(0, num_players - 1)

            game = {
                "players": names,
                "scores": [0] * num_players,
                "dealer_index": dealer_index,
                "round": 1
            }

            st.session_state.game = game
            save_game(game)

            st.session_state.page = "game"
            st.rerun()
        else:
            st.error("Please enter all player names.")


# =====================================================
# GAME PAGE
# =====================================================

def game_page():
    game = st.session_state.game

    st.title("🃏 Cribbage Tracker")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("How to Play", use_container_width=True):
            st.session_state.page = "rules"
            st.rerun()

    with col2:
        if st.button("Reset Game", use_container_width=True):
            clear_game()
            st.session_state.game = None
            st.session_state.page = "landing"
            st.rerun()

    st.markdown(f"### Round {game['round']}")
    dealer_name = game["players"][game["dealer_index"]]
    st.markdown(f"## Current Dealer: **{dealer_name}**")

    # ==========================
    # DEALER CONTROLS
    # ==========================

    with st.container(border=True):
        st.subheader("Dealer Controls")

        if st.button("Starting Jack (+2)", use_container_width=True):
            game["scores"][game["dealer_index"]] += 2
            save_game(game)
            st.rerun()

        if st.button("New Round", use_container_width=True):
            game["dealer_index"] = (game["dealer_index"] + 1) % len(game["players"])
            game["round"] += 1
            save_game(game)
            st.rerun()

    st.divider()

    # ==========================
    # PLAYER CONTAINERS
    # ==========================

    for i, player in enumerate(game["players"]):

        with st.container(border=True):

            st.subheader(player)
            st.markdown(f"### Score: {game['scores'][i]}")

            row1 = st.columns(3)
            row2 = st.columns(3)

            if row1[0].button("Made 15 (+2)", key=f"15_{i}", use_container_width=True):
                game["scores"][i] += 2
                save_game(game)
                st.rerun()

            if row1[1].button("Made 31 (+2)", key=f"31_{i}", use_container_width=True):
                game["scores"][i] += 2
                save_game(game)
                st.rerun()

            if row1[2].button("Pair (+2)", key=f"pair_{i}", use_container_width=True):
                game["scores"][i] += 2
                save_game(game)
                st.rerun()

            if row2[0].button("Triple (+6)", key=f"triple_{i}", use_container_width=True):
                game["scores"][i] += 6
                save_game(game)
                st.rerun()

            if row2[1].button("3 in a Row (+6)", key=f"run_{i}", use_container_width=True):
                game["scores"][i] += 6
                save_game(game)
                st.rerun()

            if row2[2].button("Prev Couldn't Play (+1)", key=f"go_{i}", use_container_width=True):
                game["scores"][i] += 1
                save_game(game)
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