# test_client.py

from client_transport import GameClient


# Function handling responses from server
def handle_response(response):
    
    print("Response from server:")
    print(response)


def main():

    client = GameClient("ws://127.0.0.1:8765", handle_response)
    client.connect()

    player=input("Enter player name: ")
    client.send_action("join", player_name=player)

    print("\n=== FLUJO DE JUEGO ===")
    print("1. roll_dice     - Lanza los dados")
    print("2. move_piece    - Mueve una pieza (después de lanzar dados)")
    print("3. get_pieces    - Ver posiciones de tus piezas")
    print("4. get_board     - Ver estado del tablero")
    print("5. current_player - Ver de quién es el turno")
    print("6. get_players   - Ver jugadores")
    print("7. give_sixes   - Ver jugadores")
    print("NOTA: Las piezas empiezan en cárcel (-1) y solo salen con 6\n")

    while True:
        command = input("Enter command (roll_dice/move_piece/get_pieces/give_sixes/get_board/current_player/get_players/get_my_id/exit): ").strip()
        if command == "exit":
            break
   

        if command == "get_players":
            client.send_action("get_players")   
        elif command == "current_player":
            client.send_action("current_player")
        elif command == "roll_dice":
            client.send_action("roll_dice")
        elif command == "move_piece":
            try:
                piece_id = int(input("Enter piece ID (0-3): "))
            except ValueError:
                print("❌ Invalid piece ID")
                continue

            try:
                dice_used = int(input("Enter dice to use: "))
            except ValueError:
                print("❌ Invalid dice value")
                continue

            client.send_action(
            "move_piece",
            piece_id=piece_id,
            dice_used=dice_used
            )
        elif command == "get_pieces":
            client.send_action("get_pieces")
        elif command == "get_board":
            client.send_action("get_board")     
        elif command == "get_my_id":
            client.send_action("get_my_id")
        elif command == "give_sixes":
            client.send_action("give_sixes")
        elif command == "set_piece":
            try:
                piece_id = int(input("Enter piece ID (0-3): "))
            except ValueError:
                print("❌ Invalid piece ID")
                continue
            
            try:
                position = int(input("Enter position: "))
            except ValueError:
                print("❌ Invalid dice value")
                continue

            client.send_action(
            "set_piece",
            piece_id=piece_id,
            position=position
            )
        else:
            print("Unknown command")
    
    client.close()


if __name__ == "__main__":
    main()