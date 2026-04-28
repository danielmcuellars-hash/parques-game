import uuid
from random import randint



# game_engine.py
# -------------------------------------------------
# You must implement ALL game logic in this file.
# You must design:
#   - Game state structure
#   - Board representation
#   - Player representation
#   - Turn control
# -------------------------------------------------

# Each function should return a dictionary including a "message_type" field indicating if the message is a "broadcast" (to be sent to all players)
# or a "unicast" (to be sent only to the requesting player), and the relevant data fields for the client(s) to update their state.


# Pieces colors for two players
COLORS=["red","blue"]
# Game states: waiting for players, defining turn order, in progress, finished
GAME_STATES=["waiting_for_players","defining_turn_order","in_progress","finished","dices_remaining","extra_turn"]

# Function to generate random dice rolls
def random_dices(): 
       return randint(1, 6),randint(1, 6)

# Only used during turn order definition phase
first_turn={"draw":set(),"rolls" :0,"dice_value":0,"turn":None}

# You should add more fields to board_state to represent the complete state of the board, such as the position of the pieces, the state of each player, etc. 
# For now, only the players, the current player, the dice value, and the game state are included.
board_state={    
    "players":[],
    "current_player": None,
    "dices_value": (0,0),
    "dices_remaining": [],
    "extra_turn":False,
    "game_state": GAME_STATES[0]  
}







# =================================================
# PLAYER MANAGEMENT
# =================================================

# Function called when a player joins the game. It should add the player to the game state and assign them a color. 
# If the maximum number of players is reached, it should not add more players.
# If the game is ready to start after this player joins, it should update the game state accordingly.
# The function returns a message with the updated board state to be broadcasted to all players.

def add_player(player_name,playerID):    

    global board_state
      
    if len(board_state["players"])==2:        
         return {"message_type":"broadcast","board_state": board_state}
    
   
    color=COLORS[len(board_state["players"])]
    
    board_state["players"].append({"id":playerID,"name":player_name,"color":color,"pieces":[-1,-1,-1,-1]})

    if len(board_state["players"])==2:
        board_state["game_state"]=GAME_STATES[1]
        board_state["current_player"]=board_state["players"][0]["id"]        
        return {"message_type":"broadcast","board_state": board_state}
    
    return {"message_type":"broadcast","board_state": board_state}


# This function returns the player_id of the requesting player. 
# It can be used by the client to identify itself and know which pieces belong to it, among other things.

def get_my_id(player_id):
    return {"message_type":"unicast","id": player_id}




def get_players():
    global board_state
    return {
        "message_type": "unicast",
        "players": board_state["players"]
    }


# =================================================
# TURN MANAGEMENT
# =================================================

def get_current_player():
    global board_state
    return {
        "message_type": "unicast",
        "current_player": board_state["current_player"]
    }


def next_turn():
    global board_state
    if not board_state["players"]:
        board_state["current_player"] = None
        return

    current = board_state["current_player"]
    player_ids = [p["id"] for p in board_state["players"]]
    if current not in player_ids:
        board_state["current_player"] = player_ids[0]
        return

    idx = player_ids.index(current)
    next_idx = (idx + 1) % len(player_ids)
    board_state["current_player"] = player_ids[next_idx]


# Helper function to check if it's the requesting player's turn
def is_player_turn(player_id):

    global board_state

    if board_state["current_player"]==player_id:
        return True
    return False
   




# =================================================
# DICE LOGIC
# =================================================
# The roll_dice function should handle both the turn order definition phase and the regular game phase.
def roll_dice(player_id):
    global board_state
    global first_turn

    # --- VALIDACIÓN UNIVERSAL DE TURNO ---
    if not is_player_turn(player_id):
        return {"message_type": "unicast", "error": f"No es tu turno. Turno de: {board_state['current_player']}"}

    # =========================================
    # FASE 1: DEFINIR TURNOS
    # =========================================
    if board_state["game_state"] == GAME_STATES[1]:
        dice0, dice1 = random_dices()
        board_state["dices_value"] = (dice0, dice1)
        first_turn["rolls"] += 1

        if dice0 > first_turn["dice_value"]:
            first_turn["dice_value"] = dice0
            first_turn["turn"] = player_id
            first_turn["draw"] = {player_id}
        elif dice0 == first_turn["dice_value"]:
            first_turn["draw"].add(player_id)

        player_ids = [p["id"] for p in board_state["players"]]
        idx = player_ids.index(player_id)
        board_state["current_player"] = player_ids[(idx + 1) % len(player_ids)]

        if first_turn["rolls"] == len(board_state["players"]):
            if len(first_turn["draw"]) == 1:
                board_state["current_player"] = first_turn["turn"]
                board_state["game_state"] = GAME_STATES[2]
            else:
                first_turn.update({"rolls": 0, "dice_value": 0, "turn": None, "draw": set()})
                board_state["current_player"] = board_state["players"][0]["id"]

    # =========================================
    # FASE 2: JUEGO NORMAL
    # =========================================
    elif board_state["game_state"] == GAME_STATES[2]:
        # --- BLOQUEO DE LANZAMIENTO INFINITO ---
        if board_state["dices_remaining"]:
            return {"message_type": "unicast", "error": "Ya lanzaste. Mueve tus piezas."}

        dice0, dice1 = random_dices()
        board_state["dices_value"] = (dice0, dice1)
        
        # Lógica de pares (dobles)
        if dice0 == dice1:
            board_state["dices_remaining"] = [dice0, dice1] # o [dice0]*4 según tu preferencia
            board_state["extra_turn"] = True
        else:
            board_state["dices_remaining"] = [dice0, dice1]
            board_state["extra_turn"] = False

        # Si con estos dados no puede hacer NADA, pasa el turno automáticamente
        if not player_has_moves(player_id):
            board_state["dices_remaining"] = []
            next_turn()

    return {"message_type": "broadcast", "board_state": board_state}


def give_sixes(player_id):
    global board_state

    # Solo el jugador actual puede usar el comando
    if not is_player_turn(player_id):
        return {"message_type": "unicast", "error": "No es tu turno."}
    
    # Solo funciona si el juego ya inició
    if board_state["game_state"] != GAME_STATES[2]:
        return {"message_type": "unicast", "error": "Solo puedes usar esto durante el juego."}

    # Forzamos los dados a 6
    dice0, dice1 = 6, 6
    board_state["dices_value"] = (dice0, dice1)
    board_state["dices_remaining"] = [6, 6]
    
    # Activamos turno extra por ser pares
    board_state["extra_turn"] = True

    return {"message_type": "broadcast", "board_state": board_state}
# =================================================
# PIECE MANAGEMENT
# =================================================

def get_player_pieces(player_id):
    global board_state
    player = next((p for p in board_state["players"] if p["id"] == player_id), None)
    if not player:
        return {"message_type": "unicast", "error": "Jugador no encontrado."}
    return {"message_type": "unicast", "pieces": player["pieces"]}


def get_piece_position(player_id, piece_id):
    global board_state
    player = next((p for p in board_state["players"] if p["id"] == player_id), None)
    if not player:
        return {"message_type": "unicast", "error": "Jugador no encontrado."}
    if piece_id < 0 or piece_id >= len(player["pieces"]):
        return {"message_type": "unicast", "error": "Pieza inválida."}
    return {"message_type": "unicast", "position": player["pieces"][piece_id]}


def can_piece_move(player, piece_id, dice):
    pos = player["pieces"][piece_id]
    color = player["color"]
    goal = get_home_position(color)

    if pos == -1:
        return dice == 6

    # Si ya llegó, no se mueve
    if pos == goal:
        return False

    # El movimiento debe ser EXACTO
    if pos + dice > goal:
        return False

    target_pos = pos + dice

    # --- CAMBIO AQUÍ: Si el destino es la meta, ignoramos bloqueos ---
    if target_pos == goal:
        return True

    # Bloqueo en casillas normales (2 piezas o más)
    if detect_blockade(target_pos):
        return False

    return True

def player_has_moves(player_id):
    player = next((p for p in board_state["players"] if p["id"] == player_id), None)
    if not player:
        return False

    for dice in board_state["dices_remaining"]:
        for i in range(4):
            if can_piece_move(player, i, dice):
                return True
    return False


def move_piece(player_id, piece_id, dice_used):

    global board_state

    # CONVERSIÓN DE STRING A INT
    try:
        piece_id = int(piece_id)
        if dice_used is not None:
            dice_used = int(dice_used)
    except:
        return {"message_type": "unicast", "error": "Datos inválidos."}

    # Si aún quedan dados, pero ya no hay movimientos posibles con ellos
    if board_state["dices_remaining"] and not player_has_moves(player_id):
        board_state["dices_remaining"] = [] # Limpiamos para forzar el cambio de turno

    if not is_player_turn(player_id):
        return {"message_type": "unicast", "error": "No es tu turno."}

    # AUTO-SELECCIÓN DE DADO
    if dice_used is None:
        if not board_state["dices_remaining"]:
            return {"message_type": "unicast", "error": "No hay dados disponibles."}
        dice_used = board_state["dices_remaining"][0]

    if not board_state["dices_remaining"]:
        if board_state["extra_turn"]:
            # El jugador sacó pares, se le permite volver a tirar
            board_state["extra_turn"] = False 
            board_state["dices_value"] = (0, 0)
        else:
            next_turn()
            board_state["dices_value"] = (0, 0)
               
    # Validar que el dado exista
    if dice_used not in board_state["dices_remaining"]:
        return {"message_type": "unicast", "error": "Ese dado no está disponible."}

    player = next((p for p in board_state["players"] if p["id"] == player_id), None)
    if not player:
        return {"message_type": "unicast", "error": "Jugador no encontrado."}

    pos = player["pieces"][piece_id]

    # Validar movimiento
    if not can_piece_move(player, piece_id, dice_used):
        return {"message_type": "unicast", "error": "Movimiento no válido."}

    # SALIR DE CÁRCEL
    if pos == -1:
        player["pieces"][piece_id] = get_start_position(player["color"])
        moved_to = player["pieces"][piece_id]
    else:
        moved_to = pos + dice_used
        player["pieces"][piece_id] = moved_to

    # quitar dado usado
    board_state["dices_remaining"].remove(dice_used)

    # CAPTURA
    captured = check_capture(player_id, moved_to)
    if captured:
        send_piece_home(captured["player_id"], captured["piece_id"])

    # victoria
    if has_player_won(player_id):
        board_state["game_state"] = "finished"
        return {"message_type": "broadcast", "winner": player_id, "board_state": board_state}

    # ... (dentro de move_piece, al final)
    
    # CAMBIO DE TURNO O REPETICIÓN
    if not board_state["dices_remaining"]:
        if board_state["extra_turn"]:
            # No llamamos a next_turn(), el jugador actual repite
            # Reseteamos extra_turn para el siguiente lanzamiento
            board_state["extra_turn"] = False 
            board_state["dices_value"] = (0, 0)
            # Opcional: enviar un mensaje indicando que repite tiro
        else:
            next_turn()
            board_state["dices_value"] = (0, 0)

    return {"message_type": "broadcast", "board_state": board_state}

def set_piece_position(player_id, piece_id, position):
    global board_state

    # 1. Validar turno
    if not is_player_turn(player_id):
        return {"message_type": "unicast", "error": "No es tu turno."}
    
    # 2. Convertir a enteros
    try:
        p_idx = int(piece_id)
        new_pos = int(position)
    except ValueError:
        return {"message_type": "unicast", "error": "Los argumentos deben ser números."}

    player = next((p for p in board_state["players"] if p["id"] == player_id), None)
    
    # 3. Ejecutar el movimiento manual
    if player and 0 <= p_idx < len(player["pieces"]):
        player["pieces"][p_idx] = new_pos
        
        # Limpiar dados para que el turno termine o requiera nueva acción
        board_state["dices_remaining"] = []
        board_state["dices_value"] = (0, 0)

        # 4. Verificar si con este movimiento el jugador ganó
        if has_player_won(player_id):
            board_state["game_state"] = "finished"
            return {"message_type": "broadcast", "winner": player_id, "board_state": board_state}

        return {"message_type": "broadcast", "board_state": board_state}
    
    return {"message_type": "unicast", "error": "Pieza no encontrada."}
# =================================================
# BOARD LOGIC
# =================================================

# Casillas de salida y meta para cada color
START_POSITIONS = {
    "red": 0,
    "blue": 17
}
HOME_POSITIONS = {
    "red": 56,
    "blue": 73
}

def get_start_position(color):
    """
    Retorna la casilla de salida para el color dado.
    """
    return START_POSITIONS.get(color, 0)

def get_home_position(color):
    """
    Retorna la casilla de meta para el color dado.
    """
    return HOME_POSITIONS.get(color, 56)

def get_board():
    global board_state
    return {"message_type": "unicast", "board_state": board_state}





def is_safe_square(position):
    # Ejemplo: casillas de seguro clásicas
    safe_squares = [0, 8, 17, 25, 34, 42, 51, 56, 73]
    return position in safe_squares


def detect_blockade(position):
    global board_state
    count = 0
    for player in board_state["players"]:
        count += player["pieces"].count(position)
    return count >= 2


# =================================================
# CAPTURE & RULES
# =================================================

def check_capture(player_id, position):
    global board_state
    for player in board_state["players"]:
        if player["id"] != player_id:
            for idx, piece_pos in enumerate(player["pieces"]):
                if piece_pos == position and not is_safe_square(position):
                    return {"player_id": player["id"], "piece_id": idx}
    return None


def send_piece_home(player_id, piece_id):
    
    global board_state
    player = next((p for p in board_state["players"] if p["id"] == player_id), None)
    if player:
        player["pieces"][piece_id] = -1


def can_exit_jail():
    return 6 in board_state["dices_remaining"]


# =================================================
# WIN CONDITION
# =================================================

def has_player_won(player_id):
   
    global board_state
    player = next((p for p in board_state["players"] if p["id"] == player_id), None)
    if not player:
        return False
    home = get_home_position(player["color"])
    return all(pos == home for pos in player["pieces"])


def check_game_finished():
    
    global board_state
    for player in board_state["players"]:
        if has_player_won(player["id"]):
            return True
    return False


# =================================================
# GAME STATE
# =================================================

def get_game_status():
    
    global board_state
    return {"message_type": "unicast", "game_state": board_state["game_state"]}


def get_state():
    
    global board_state
    return {"message_type": "unicast", "state": board_state}