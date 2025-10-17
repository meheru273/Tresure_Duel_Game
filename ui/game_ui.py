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

# Game constants
WINDOW_SIZE = 900
GRID_SIZE = 4
CELL_SIZE = WINDOW_SIZE // (GRID_SIZE + 3)
GRID_OFFSET = CELL_SIZE
UI_PANEL_HEIGHT = 120


class PygameUI:
    """Graphical user interface for Treasure Duel using Pygame."""
    
    def __init__(self, grid_size=4, num_treasures=5, ai_depth=4):
        """Initialize pygame and game state."""
        pygame.init()
        
        self.grid_size = grid_size
        self.num_treasures = num_treasures
        self.ai_depth = ai_depth
        
        # Setup display
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + UI_PANEL_HEIGHT))
        pygame.display.set_caption("Treasure Duel - AI Strategy Game")
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Game state
        self.state = None
        self.selected_move = None
        self.legal_moves = []
        self.game_over = False
        self.game_started = False
        self.game_state = "start"  # start, playing, game_over, no_moves
        
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
        self.game_started = False
        self.game_state = "start"
        self.update_legal_moves()
        
    def update_legal_moves(self):
        """Update the list of legal moves for current player."""
        if self.state and not is_terminal(self.state):
            self.legal_moves = get_legal_moves(self.state)
            # Check if no moves available for current player
            if not self.legal_moves:
                # Check if other player also has no moves
                temp_state = self.state.copy()
                temp_state.is_human_turn = not temp_state.is_human_turn
                other_moves = get_legal_moves(temp_state)
                if not other_moves:
                    self.game_state = "no_moves"
                    self.game_over = True
                else:
                    # Switch to other player
                    self.state.is_human_turn = not self.state.is_human_turn
                    self.legal_moves = get_legal_moves(self.state)
        else:
            self.legal_moves = []
            if self.state and is_terminal(self.state):
                self.game_state = "game_over"
                self.game_over = True
            
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
                    color = DARK_GRAY
                elif self.game_state == "playing" and pos in self.legal_moves:
                    color = GREEN
                else:
                    color = LIGHT_GRAY
                
                # Draw cell
                pygame.draw.rect(self.screen, color, 
                               (screen_x, screen_y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, BLACK, 
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
    
    def draw_start_screen(self):
        """Draw the start screen overlay."""
        if self.game_state != "start":
            return
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_text = "TREASURE DUEL"
        title = self.font_large.render(title_text, True, GOLD)
        title_rect = title.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 100))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle_text = "AI Strategy Game"
        subtitle = self.font_medium.render(subtitle_text, True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 60))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instructions
        instructions = [
            "• Collect treasures to increase your score",
            "• Some treasures have negative values!",
            "• Human starts at top-left (H)",
            "• AI starts at bottom-right (A)",
            "• Click anywhere to start!"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 20 + i * 25))
            self.screen.blit(text, text_rect)
    
    def draw_ui(self):
        """Draw UI elements (scores, turn indicator, game state)."""
        # Draw UI panel background
        ui_panel_rect = pygame.Rect(0, WINDOW_SIZE, WINDOW_SIZE, UI_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, LIGHT_GRAY, ui_panel_rect)
        pygame.draw.rect(self.screen, BLACK, ui_panel_rect, 2)
        
        # Scoreboard section
        self.draw_scoreboard()
        
        # Game state section
        self.draw_game_state()
        
        # Instructions section
        self.draw_instructions()
    
    def draw_scoreboard(self):
        """Draw the scoreboard with enhanced visual design."""
        # Scoreboard background
        scoreboard_rect = pygame.Rect(20, WINDOW_SIZE + 10, WINDOW_SIZE - 40, 50)
        pygame.draw.rect(self.screen, WHITE, scoreboard_rect)
        pygame.draw.rect(self.screen, BLACK, scoreboard_rect, 2)
        
        # Human score
        human_score_rect = pygame.Rect(30, WINDOW_SIZE + 20, 200, 30)
        pygame.draw.rect(self.screen, BLUE, human_score_rect)
        human_text = f"Human: {self.state.human_score}"
        text = self.font_medium.render(human_text, True, WHITE)
        text_rect = text.get_rect(center=human_score_rect.center)
        self.screen.blit(text, text_rect)
        
        # AI score
        ai_score_rect = pygame.Rect(250, WINDOW_SIZE + 20, 200, 30)
        pygame.draw.rect(self.screen, PURPLE, ai_score_rect)
        ai_text = f"AI: {self.state.ai_score}"
        text = self.font_medium.render(ai_text, True, WHITE)
        text_rect = text.get_rect(center=ai_score_rect.center)
        self.screen.blit(text, text_rect)
        
        # Score difference
        score_diff = self.state.ai_score - self.state.human_score
        diff_text = f"Difference: {score_diff:+d}"
        diff_color = RED if score_diff > 0 else GREEN if score_diff < 0 else BLACK
        text = self.font_small.render(diff_text, True, diff_color)
        text_rect = text.get_rect(center=(WINDOW_SIZE - 100, WINDOW_SIZE + 35))
        self.screen.blit(text, text_rect)
    
    def draw_game_state(self):
        """Draw the current game state indicator."""
        state_y = WINDOW_SIZE + 70
        
        if self.game_state == "start":
            state_text = "Click anywhere to start the game!"
            state_color = GREEN
        elif self.game_state == "playing":
            if self.state.is_human_turn:
                state_text = "Your Turn - Click a green cell to move"
                state_color = BLUE
            else:
                state_text = "AI is thinking..."
                state_color = PURPLE
        elif self.game_state == "no_moves":
            state_text = "No moves available - Game Over!"
            state_color = RED
        elif self.game_state == "game_over":
            winner = get_winner(self.state)
            if winner == "Human":
                state_text = "🎉 You Win! 🎉"
                state_color = GREEN
            elif winner == "AI":
                state_text = "🤖 AI Wins! 🤖"
                state_color = RED
            else:
                state_text = "🤝 It's a Draw! 🤝"
                state_color = GOLD
        
        text = self.font_medium.render(state_text, True, state_color)
        text_rect = text.get_rect(center=(WINDOW_SIZE//2, state_y))
        self.screen.blit(text, text_rect)
    
    def draw_instructions(self):
        """Draw game instructions and controls."""
        instructions = [
            "Press R to restart | Click green cells to move",
            f"Treasures remaining: {len(self.state.treasures)}"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_tiny.render(instruction, True, DARK_GRAY)
            text_rect = text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE + 100 + i * 15))
            self.screen.blit(text, text_rect)
    
    def handle_click(self, pos):
        """Handle mouse click events."""
        # Handle start screen
        if self.game_state == "start":
            self.game_started = True
            self.game_state = "playing"
            return
        
        # Handle game over states
        if self.game_over or self.game_state != "playing":
            return
        
        # Handle human turn
        if not self.state.is_human_turn:
            return
        
        grid_pos = self.screen_to_grid(pos)
        if grid_pos and grid_pos in self.legal_moves:
            self.state = self.state.apply_move(grid_pos)
            self.update_legal_moves()
            
            if is_terminal(self.state):
                self.game_state = "game_over"
                self.game_over = True
    
    def ai_move(self):
        """Execute AI move."""
        if not self.state.is_human_turn and not self.game_over and self.game_state == "playing":
            best_move = get_best_move(self.state, depth=self.ai_depth, use_alpha_beta=True)
            if best_move:
                pygame.time.delay(500)  # Brief delay for visual effect
                self.state = self.state.apply_move(best_move)
                self.update_legal_moves()
                
                if is_terminal(self.state):
                    self.game_state = "game_over"
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
            if not self.state.is_human_turn and not self.game_over and self.game_started:
                self.ai_move()
            
            # Drawing
            self.screen.fill(WHITE)
            self.draw_grid()
            self.draw_start_screen()
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
