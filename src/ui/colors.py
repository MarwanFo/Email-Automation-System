"""
Nordic Minimalism Color Palette

Inspired by Scandinavian design principles: clean, functional,
and warm despite the cool tones. We picked these after trying
about 47 different combinations — trust us, these work.
"""

# Primary palette — the foundation of our visual identity
PRIMARY = "#2C3E50"       # Deep Blue-Gray: headers, emphasis, serious stuff
SECONDARY = "#E8F4F8"     # Soft Ice Blue: backgrounds, subtle highlights
ACCENT = "#F39C12"        # Warm Amber: CTAs, important actions, that pop of warmth

# Text hierarchy — because readable is beautiful
TEXT_PRIMARY = "#34495E"  # Charcoal: body text, most readable
TEXT_MUTED = "#7F8C8D"    # Slate Gray: secondary info, timestamps
TEXT_LIGHT = "#BDC3C7"    # Silver: placeholders, disabled states

# Semantic colors — instant meaning without thinking
SUCCESS = "#27AE60"       # Forest Green: wins, confirmations, go-ahead
ERROR = "#E74C3C"         # Terracotta Red: problems, but not scary-red
WARNING = "#F39C12"       # Same as accent: attention needed, not panic
INFO = "#3498DB"          # Clear Blue: tips, helpful nudges

# Rich console color names (for Rich library compatibility)
RICH_COLORS = {
    "primary": "color(60)",      # Approximates #2C3E50
    "secondary": "color(195)",   # Approximates #E8F4F8
    "accent": "color(214)",      # Approximates #F39C12
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "blue",
    "muted": "dim white",
}


def get_rich_style(color_name: str) -> str:
    """
    Get a Rich-compatible style string for our color palette.
    
    We bridge the gap between our hex colors and Rich's color system
    so you can use our palette names everywhere.
    """
    return RICH_COLORS.get(color_name, "white")
