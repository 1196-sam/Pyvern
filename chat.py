import pygame, socket, threading, traceback, sys,json
from datetime import datetime
CONFIG_PATH = "userconfig.json"

# Default fallback config (if file missing or broken)
default_config = {
    "username": "User",
    "network": {
        "tcp_port": 5050,
        "scan_timeout": 0.4
    },
    "appearance": {
        "font_name": "Arial",
        "background_color": [0, 0, 0],
        "text_color": [0, 255, 0],
        "input_background": [40, 40, 40]
    }
}

try:
    with open(CONFIG_PATH, "r") as f:
        user_config = json.load(f)
except Exception as e:
    print(f"[WARN] Could not load {CONFIG_PATH}, using defaults. ({e})")
    user_config = default_config

# Extract config values
USERNAME = user_config.get("username", default_config["username"])
TCP_PORT = user_config.get("network", {}).get("tcp_port", default_config["network"]["tcp_port"])
SCAN_TIMEOUT = user_config.get("network", {}).get("scan_timeout", default_config["network"]["scan_timeout"])
FONT_NAME = user_config.get("appearance", {}).get("font_name", default_config["appearance"]["font_name"])
BG_COLOR = tuple(user_config.get("appearance", {}).get("background_color", default_config["appearance"]["background_color"]))
TEXT_COLOR = tuple(user_config.get("appearance", {}).get("text_color", default_config["appearance"]["text_color"]))
INPUT_BG = tuple(user_config.get("appearance", {}).get("input_background", default_config["appearance"]["input_background"]))

allowed_inputs = ["a","b","c","d","e","f","g","h","i","j","k","l","m"
                  "n","o","p","q","r","s","t","u","v","w","x","y","z"
                  "0","1","2","3","4","5","6","7","8","9",",",":","("
                  ")","[","]",";","'",'"',"#","!","?","%","^","*","&",
                  "£","$"]
# === NETWORK HELPERS ===
def get_local_ip():
    """Get active LAN IP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def try_connect_subnet(local_ip):
    """Scan subnet for open server."""
    subnet = ".".join(local_ip.split(".")[:-1]) + "."
    print("searching all available ips")
    print(f"[SCAN] Searching {subnet}0–255 for active servers...")
    for i in range(0,255):  # adjustable range     ####PRINT I
        target = subnet + str(i)
        if target == local_ip:
            continue
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SCAN_TIMEOUT)
        try:
            s.connect((target, TCP_PORT))
            print(f"[CLIENT] Connected to server at {target}")
            return s
        except (socket.timeout, ConnectionRefusedError):
            s.close()
            continue
        except Exception as e:
            print(f"[DEBUG] Connection error to {target}: {e}")
            s.close()
    return None

def start_server(local_ip):
    """Wait for client connection."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((local_ip, TCP_PORT))
    s.listen(1)
    print(f"[SERVER] Waiting on {local_ip}:{TCP_PORT}...")
    conn, addr = s.accept()
    print(f"[SERVER] Connected with {addr[0]}")
    return conn

# === PYGAME CHAT ===
def run_chat(conn):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("LAN Chat")
    font = pygame.font.SysFont(FONT_NAME, 22)
    clock = pygame.time.Clock()

    messages = []
    input_text = ""
    scroll = 0
    running = True

    def render_text(text, color, y):
        surf = font.render(text, True, color)
        screen.blit(surf, (10, y))

    def listen_thread():
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    messages.append("[INFO] Peer disconnected.")
                    break
                msg = data.decode()
                messages.append(f"[Peer] {msg}")
            except Exception as e:
                messages.append(f"[ERROR] Listening error: {e}")
                break

    threading.Thread(target=listen_thread, daemon=True).start()

    while running:
        clock.tick(30)
        screen.fill(BG_COLOR)

        # --- Draw messages ---
        y = 10
        for msg in messages[-25 + scroll:]:
            render_text(msg, TEXT_COLOR, y)
            y += 25

        # --- Input bar ---
        pygame.draw.rect(screen, INPUT_BG, (0, 570, 800, 30))
        render_text("> " + input_text, TEXT_COLOR, 575)

        pygame.display.flip()

        # --- Handle events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                conn.close()
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text.strip():
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        msg = f"{input_text}  ({timestamp})"
                        try:
                            conn.sendall(msg.encode())
                            messages.append(f"[You] {msg}")
                        except Exception as e:
                            messages.append(f"[ERROR] Send failed: {e}")
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_UP:
                    scroll = min(scroll + 1, len(messages))
                elif event.key == pygame.K_DOWN:
                    scroll = max(scroll - 1, 0)
                else:
                    input_text += event.unicode

    conn.close()

# === MAIN ===
if __name__ == "__main__":
    try:
        local_ip = get_local_ip()
        print(f"[INFO] Local IP: {local_ip}")
        conn = try_connect_subnet(local_ip)
        if not conn:
            print("[ROLE] No server detected — starting as server.")
            conn = start_server(local_ip)
        else:
            print("[ROLE] Acting as client.")
        conn.settimeout(None)
        run_chat(conn)
    except Exception:
        traceback.print_exc()
        input("\nPress Enter to exit...")

