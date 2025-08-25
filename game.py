import pygame
import socket
import pickle

# --- Constants ---
# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Paddle properties
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
BALL_RADIUS = 10
PADDLE_SPEED = 7

# --- Network Settings ---
SERVER_IP = "YOUR_SERVER_IP_HERE"
PORT = 65432

# --- Game Setup ---
def setup_network():
    """Connects to the server."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((SERVER_IP, PORT))
        print("Connected to server.")
        return s
    except socket.error as e:
        print(f"Connection failed: {e}")
        return None

def main():
    """Main game function for the client."""
    # --- Network Initialization ---
    connection = setup_network()
    if not connection:
        return # Exit if connection failed

    # --- Pygame Initialization ---
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ping Pong - Client (Player 2)")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 74)

    # --- Game Objects (Client only controls its own paddle) ---
    # Player 1 (Server) paddle - position will be updated from network
    player1_paddle = pygame.Rect(30, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    # Player 2 (Client) paddle
    player2_paddle = pygame.Rect(SCREEN_WIDTH - 30 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    # Ball - position will be updated from network
    ball = pygame.Rect(0, 0, BALL_RADIUS * 2, BALL_RADIUS * 2) # Initial position doesn't matter
    
    # Scores - will be updated from network
    player1_score = 0
    player2_score = 0

    # --- Game Loop ---
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Player 2 (Client) Movement ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and player2_paddle.top > 0:
            player2_paddle.y -= PADDLE_SPEED
        if keys[pygame.K_DOWN] and player2_paddle.bottom < SCREEN_HEIGHT:
            player2_paddle.y += PADDLE_SPEED

        # --- Network Communication ---
        try:
            # Send this client's paddle position to the server
            connection.sendall(pickle.dumps(player2_paddle.y))

            # Receive the full game state from the server
            data = connection.recv(4096)
            if not data:
                print("Server disconnected.")
                break
            game_state = pickle.loads(data)
            
            # Update local game objects based on server's state
            player1_paddle.y = game_state['player1_y']
            ball.x = game_state['ball_x']
            ball.y = game_state['ball_y']
            player1_score = game_state['score1']
            player2_score = game_state['score2']

        except (ConnectionResetError, BrokenPipeError, EOFError):
            print("Connection to server lost.")
            running = False

        # --- Drawing ---
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, player1_paddle)
        pygame.draw.rect(screen, WHITE, player2_paddle)
        pygame.draw.ellipse(screen, WHITE, ball)
        pygame.draw.aaline(screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))

        # Draw scores
        score1_text = font.render(str(player1_score), True, WHITE)
        screen.blit(score1_text, (SCREEN_WIDTH // 4, 10))
        score2_text = font.render(str(player2_score), True, WHITE)
        screen.blit(score2_text, (SCREEN_WIDTH * 3 // 4 - score2_text.get_width(), 10))

        # --- Update Display ---
        pygame.display.flip()
        
        # --- Check for winner ---
        if player1_score >= 10 or player2_score >= 10:
            running = False

        # --- Frame Rate ---
        clock.tick(60)

    # --- Cleanup ---
    connection.close()
    pygame.quit()

if __name__ == "__main__":
    main()

