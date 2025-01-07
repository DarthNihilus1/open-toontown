LIGHT_GREEN = "Green"
LIGHT_RED = "Red"
# Game duration in seconds
GAME_DURATION = 120

# Minimum and maximum time the light stays green or red
GREEN_LIGHT_DURATION_RANGE = (5, 10)  # Seconds
RED_LIGHT_DURATION_RANGE = (3, 7)    # Seconds

# Time penalty for a Toon eliminated
ELIMINATION_DELAY = 2  # Seconds before the Toon is marked sad



# Starting positions for players (adjust based on factory layout)
STARTING_POSITIONS = [(0, 0, 0), (2, 0, 0), (-2, 0, 0), (4, 0, 0)]

# Goal position (adjust based on factory layout)
GOAL_POSITION = (100, 0, 0)  # Game units

# Distance to the goal that counts as "reaching it"
GOAL_RADIUS = 5.0  # Units

# Light state colors
RED_LIGHT_COLOR = (1, 0, 0, 1)  # RGBA for Red
GREEN_LIGHT_COLOR = (0, 1, 0, 1)  # RGBA for Green

# Sound effects for transitions
RED_LIGHT_SOUND = "phase_4/audio/sfx/red_light.ogg"
GREEN_LIGHT_SOUND = "phase_4/audio/sfx/green_light.ogg"

# Elimination animation
ELIMINATION_ANIMATION = "sad_walk"

# Rewards for reaching the goal (applied to all remaining Toons)
REWARD_POINTS = 20

# Penalty for getting eliminated (applied to all remaining Toons)
PENALTY_POINTS = -20

# Bonus for the fastest Toon to the goal
FASTEST_TOON_BONUS = 25

# Cog observer details
COG_NAME = "Foreman"
COG_POSITION = (50, 0, 10)  # Position in the factory
COG_ROTATION_SPEED = 90  # Degrees per second (for turning head, if animated)

# Button objective (lore-based action)
BUTTON_POSITION = (105, 0, 0)  # Near the goal


