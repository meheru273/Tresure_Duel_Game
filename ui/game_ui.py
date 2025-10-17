import pygame
import sys
from game.state import GameState
from game.rules import get_legal_moves, is_terminal, get_winner
from game.engine import get_best_move, clear_transposition_table
import random

# Color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (240, 240, 240)
DARK_GRAY = (100, 100, 100)
BLUE = (100, 150, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
GOLD = (255, 215, 0)
PURPLE = (200, 100, 255)
# New colors for visited cells
VISITED_COLOR = (150, 150, 200)  # Light blue-gray for visited cells
VISITED_BORDER = (100, 100, 150)  # Darker border for visited cells

# Game constants
WINDOW_SIZE = 800
GRID_SIZE = 4
CELL_SIZE = WINDOW_SIZE // (GRID_SIZE + 2)
GRID_OFFSET = CELL_SIZE


class PygameUI:
    """Graphical user interface for Treasure Duel using Pygame."""
    
    def __init__(self, grid_size=4, num_treasures=5, ai_depth=4):
        """Initialize pygame and game state."""
        pygame.init()
        
        self.grid_size = grid_size
        self.num_treasures = num_treasures
        self.ai_depth = ai_depth
        
        # Setup display
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Treasure Duel - AI Strategy Game")
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Game state
        self.state = None
        self.selected_move = None
        self.legal_moves = []
        self.game_over = False
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        
    def initialize_game(self):
        """Initialize a new game."""
        clear_transposition_table()
        self.state = GameState(grid_size=self.grid_size)
        
        # Generate random treasures
        available_cells = []
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                if (x, y) not in [(0, 0), (self.grid_size-1, self.grid_size-1)]:
                    available_cells.append((x, y))
        
        treasure_positions = random.sample(available_cells, min(self.num_treasures, len(available_cells)))
        treasures = {}
        for pos in treasure_positions:
            value = random.randint(-3, 10)
            treasures[pos] = value
        
        self.state.treasures = treasures
        self.game_over = False
        self.update_legal_moves()
        
    def update_legal_moves(self):
        """Update the list of legal moves for current player."""
        if self.state and not is_terminal(self.state):
            self.legal_moves = get_legal_moves(self.state)
        else:
            self.legal_moves = []
            
    def grid_to_screen(self, grid_pos):
        """Convert grid coordinates to screen coordinates."""
        x, y = grid_pos
        screen_x = GRID_OFFSET + y * CELL_SIZE
        screen_y = GRID_OFFSET + x * CELL_SIZE
        return screen_x, screen_y
    
    def screen_to_grid(self, screen_pos):
        """Convert screen coordinates to grid coordinates."""
        screen_x, screen_y = screen_pos
        x = (screen_y - GRID_OFFSET) // CELL_SIZE
        y = (screen_x - GRID_OFFSET) // CELL_SIZE
        
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return (x, y)
        return None
    
    def draw_grid(self):
        """Draw the game grid."""
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                pos = (x, y)
                screen_x, screen_y = self.grid_to_screen(pos)
                
                # Determine cell color
                if pos in self.state.visited:
                    color = VISITED_COLOR
                elif pos in self.legal_moves:
                    color = GREEN
                else:
                    color = LIGHT_GRAY
                
                # Draw cell
                pygame.draw.rect(self.screen, color, 
                               (screen_x, screen_y, CELL_SIZE, CELL_SIZE))
                # Use different border color for visited cells
                border_color = VISITED_BORDER if pos in self.state.visited else BLACK
                pygame.draw.rect(self.screen, border_color, 
                               (screen_x, screen_y, CELL_SIZE, CELL_SIZE), 2)
                
                # Draw treasures
                if pos in self.state.treasures:
                    value = self.state.treasures[pos]
                    treasure_color = GOLD if value > 0 else RED
                    pygame.draw.circle(self.screen, treasure_color,
                                     (screen_x + CELL_SIZE//2, screen_y + CELL_SIZE//2),
                                     CELL_SIZE//4)
                    
                    # Draw treasure value
                    text = self.font_small.render(f"{value:+d}", True, BLACK)
                    text_rect = text.get_rect(center=(screen_x + CELL_SIZE//2, 
                                                      screen_y + CELL_SIZE//2))
                    self.screen.blit(text, text_rect)
        
        # Draw players
        # Human player
        human_x, human_y = self.grid_to_screen(self.state.human_pos)
        pygame.draw.circle(self.screen, BLUE,
                         (human_x + CELL_SIZE//2, human_y + CELL_SIZE//2),
                         CELL_SIZE//3)
        text = self.font_medium.render("H", True, WHITE)
        text_rect = text.get_rect(center=(human_x + CELL_SIZE//2, human_y + CELL_SIZE//2))
        self.screen.blit(text, text_rect)
        
        # AI player
        ai_x, ai_y = self.grid_to_screen(self.state.ai_pos)
        pygame.draw.circle(self.screen, PURPLE,
                         (ai_x + CELL_SIZE//2, ai_y + CELL_SIZE//2),
                         CELL_SIZE//3)
        text = self.font_medium.render("A", True, WHITE)
        text_rect = text.get_rect(center=(ai_x + CELL_SIZE//2, ai_y + CELL_SIZE//2))
        self.screen.blit(text, text_rect)
    
    def draw_ui(self):
        """Draw UI elements (scores, turn indicator)."""
        # Score display
        score_text = f"Human: {self.state.human_score}  |  AI: {self.state.ai_score}"
        text = self.font_medium.render(score_text, True, BLACK)
        self.screen.blit(text, (20, 20))
        
        # Turn indicator
        if not self.game_over:
            turn_text = "Your Turn" if self.state.is_human_turn else "AI Thinking..."
            turn_color = BLUE if self.state.is_human_turn else PURPLE
        else:
            winner = get_winner(self.state)
            turn_text = f"Game Over! Winner: {winner}"
            turn_color = GREEN if winner == "Human" else RED if winner == "AI" else BLACK
        
        text = self.font_medium.render(turn_text, True, turn_color)
        text_rect = text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE - 40))
        self.screen.blit(text, text_rect)
        
        # Instructions
        if self.state.is_human_turn and not self.game_over:
            instr_text = "Click a green cell to move"
            text = self.font_small.render(instr_text, True, DARK_GRAY)
            text_rect = text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE - 70))
            self.screen.blit(text, text_rect)
    
    def handle_click(self, pos):
        """Handle mouse click events."""
        if self.game_over or not self.state.is_human_turn:
            return
        
        grid_pos = self.screen_to_grid(pos)
        if grid_pos and grid_pos in self.legal_moves:
            self.state = self.state.apply_move(grid_pos)
            self.update_legal_moves()
            
            if is_terminal(self.state):
                self.game_over = True
    
    def ai_move(self):
        """Execute AI move."""
        if not self.state.is_human_turn and not self.game_over:
            best_move = get_best_move(self.state, depth=self.ai_depth, use_alpha_beta=True)
            if best_move:
                pygame.time.delay(500)  # Brief delay for visual effect
                self.state = self.state.apply_move(best_move)
                self.update_legal_moves()
                
                if is_terminal(self.state):
                    self.game_over = True
    
    def run(self):
        """Main game loop."""
        self.initialize_game()
        
        running = True
        while running:
            self.clock.tick(60)  # 60 FPS
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Press R to restart
                        self.initialize_game()
            
            # AI move
            if not self.state.is_human_turn and not self.game_over:
                self.ai_move()
            
            # Drawing
            self.screen.fill(WHITE)
            self.draw_grid()
            self.draw_ui()
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


def main():
    """Entry point for pygame UI."""
    ui = PygameUI(grid_size=4, num_treasures=5, ai_depth=4)
    ui.run()


if __name__ == "__main__":
    main()
