# server.py
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

# Paddle and Ball properties
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
BALL_RADIUS = 10
PADDLE_SPEED = 7
BALL_SPEED_X = 5
BALL_SPEED_Y = 5

# Network settings
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 65432

# --- Game Setup ---
def setup_network():
    """Sets up the server socket and waits for a client connection."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    print("Waiting for a connection...")
    conn, addr = s.accept()
    print(f"Connected by {addr}")
    return conn

def main():
    """Main game function for the server."""
    # --- Network Initialization ---
    connection = setup_network()

    # --- Pygame Initialization ---
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ping Pong - Server (Player 1)")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 74)

    # --- Game Objects ---
    # Player 1 (Server) paddle on the left
    player1_paddle = pygame.Rect(30, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    # Player 2 (Client) paddle on the right
    player2_paddle = pygame.Rect(SCREEN_WIDTH - 30 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    # Ball
    ball = pygame.Rect(SCREEN_WIDTH // 2 - BALL_RADIUS, SCREEN_HEIGHT // 2 - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
    ball_speed_x = BALL_SPEED_X
    ball_speed_y = BALL_SPEED_Y

    # --- Score ---
    player1_score = 0
    player2_score = 0
    
    # --- Game Loop ---
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Player 1 (Server) Movement ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and player1_paddle.top > 0:
            player1_paddle.y -= PADDLE_SPEED
        if keys[pygame.K_s] and player1_paddle.bottom < SCREEN_HEIGHT:
            player1_paddle.y += PADDLE_SPEED

        # --- Ball Movement and Logic ---
        ball.x += ball_speed_x
        ball.y += ball_speed_y

        # Ball collision with top/bottom walls
        if ball.top <= 0 or ball.bottom >= SCREEN_HEIGHT:
            ball_speed_y *= -1

        # Ball collision with paddles
        if ball.colliderect(player1_paddle) or ball.colliderect(player2_paddle):
            ball_speed_x *= -1
            
        # Scoring
        if ball.left <= 0:
            player2_score += 1
            ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            ball_speed_x *= -1 # Start towards the other player
        if ball.right >= SCREEN_WIDTH:
            player1_score += 1
            ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            ball_speed_x *= -1 # Start towards the other player

        # --- Network Communication ---
        try:
            # Send game state to client
            # State includes: server paddle y, ball x, ball y, scores
            game_state = {
                'player1_y': player1_paddle.y,
                'ball_x': ball.x,
                'ball_y': ball.y,
                'score1': player1_score,
                'score2': player2_score
            }
            connection.sendall(pickle.dumps(game_state))

            # Receive client's paddle position
            data = connection.recv(1024)
            if not data:
                print("Client disconnected.")
                break
            client_paddle_y = pickle.loads(data)
            player2_paddle.y = client_paddle_y
        except (ConnectionResetError, BrokenPipeError):
            print("Client connection lost.")
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
