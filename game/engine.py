from typing import Tuple, Optional, Dict
from state import GameState
from rules import get_legal_moves, is_terminal
from heuristics import evaluate_state

# Transposition table for memoization
transposition_table: Dict[int, Tuple[float, int]] = {}


def clear_transposition_table():
    """Clear the transposition table (call between games)."""
    global transposition_table
    transposition_table = {}


def order_moves(state: GameState, moves: list) -> list:
    """
    Order moves for better alpha-beta pruning efficiency.

    Prioritizes moves that:
    1. Collect treasures (especially high-value ones)
    2. Move toward nearest treasure
    3. Maintain mobility

    Args:
        state: Current game state
        moves: List of legal moves

    Returns:
        Sorted list of moves (best first)
    """
    def move_priority(move):
        priority = 0

        # Highest priority: moves that collect treasure
        if move in state.treasures:
            priority += state.treasures[move] * 1000

        # Secondary: distance to nearest treasure after move
        if state.treasures:
            min_dist = float('inf')
            for treasure_pos in state.treasures.keys():
                dist = abs(move[0] - treasure_pos[0]) + abs(move[1] - treasure_pos[1])
                min_dist = min(min_dist, dist)
            priority -= min_dist

        return priority

    return sorted(moves, key=move_priority, reverse=True)


def minimax(state: GameState, depth: int, maximizing_player: bool) -> Tuple[float, Optional[Tuple[int, int]]]:
    """
    Basic minimax algorithm without pruning.

    Args:
        state: Current game state
        depth: Maximum search depth
        maximizing_player: True if AI (maximizing), False if human (minimizing)

    Returns:
        Tuple of (best_value, best_move)
    """
    # Terminal condition or depth limit
    if depth == 0 or is_terminal(state):
        return evaluate_state(state), None

    moves = get_legal_moves(state)

    # No moves available
    if not moves:
        return evaluate_state(state), None

    best_move = None

    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            new_state = state.apply_move(move)
            eval_score, _ = minimax(new_state, depth - 1, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_state = state.apply_move(move)
            eval_score, _ = minimax(new_state, depth - 1, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
        return min_eval, best_move


def alpha_beta(state: GameState, depth: int, alpha: float, beta: float, 
               maximizing_player: bool, use_tt: bool = True) -> Tuple[float, Optional[Tuple[int, int]]]:
    """
    Minimax with alpha-beta pruning and optional transposition table.

    Args:
        state: Current game state
        depth: Maximum search depth
        alpha: Alpha value for pruning
        beta: Beta value for pruning
        maximizing_player: True if AI (maximizing), False if human (minimizing)
        use_tt: Whether to use transposition table

    Returns:
        Tuple of (best_value, best_move)
    """
    # Check transposition table
    state_hash = hash(state)
    if use_tt and state_hash in transposition_table:
        cached_value, cached_depth = transposition_table[state_hash]
        if cached_depth >= depth:
            return cached_value, None

    # Terminal condition or depth limit
    if depth == 0 or is_terminal(state):
        eval_score = evaluate_state(state)
        if use_tt:
            transposition_table[state_hash] = (eval_score, depth)
        return eval_score, None

    moves = get_legal_moves(state)

    # No moves available
    if not moves:
        eval_score = evaluate_state(state)
        if use_tt:
            transposition_table[state_hash] = (eval_score, depth)
        return eval_score, None

    # Move ordering for better pruning
    moves = order_moves(state, moves)

    best_move = moves[0]  # Default to first move

    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            new_state = state.apply_move(move)
            eval_score, _ = alpha_beta(new_state, depth - 1, alpha, beta, False, use_tt)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff

        if use_tt:
            transposition_table[state_hash] = (max_eval, depth)
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_state = state.apply_move(move)
            eval_score, _ = alpha_beta(new_state, depth - 1, alpha, beta, True, use_tt)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff

        if use_tt:
            transposition_table[state_hash] = (min_eval, depth)
        return min_eval, best_move


def get_best_move(state: GameState, depth: int = 4, use_alpha_beta: bool = True) -> Tuple[int, int]:
    """
    Get the best move for the current player using AI search.

    Args:
        state: Current game state
        depth: Search depth (default: 4)
        use_alpha_beta: Use alpha-beta pruning (True) or basic minimax (False)

    Returns:
        Best move as (x, y) tuple
    """
    is_maximizing = not state.is_human_turn  # AI is maximizing player

    if use_alpha_beta:
        _, best_move = alpha_beta(state, depth, float('-inf'), float('inf'), is_maximizing)
    else:
        _, best_move = minimax(state, depth, is_maximizing)

    # Fallback to first legal move if no move found
    if best_move is None:
        moves = get_legal_moves(state)
        if moves:
            best_move = moves[0]

    return best_move