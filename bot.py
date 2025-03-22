from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import logging

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states for conversation
INPUT_NAME, INPUT_ROLE, INPUT_CREDIT, INPUT_POINTS, INPUT_PITCH, INPUT_STATS = range(6)

# Store player data
players = []

# Start command
async def start(update: Update, context):
    await update.message.reply_text(
        "Welcome to the Dream11 Team Maker Bot!\n\n"
        "Use /addplayer to add a new player.\n"
        "Use /maketeam to generate a team."
    )

# Add player command
async def add_player(update: Update, context):
    await update.message.reply_text("Enter the player's name:")
    return INPUT_NAME

# Input player name
async def input_name(update: Update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Enter the player's role (Batsman, Bowler, All-rounder, Wicket-keeper):")
    return INPUT_ROLE

# Input player role
async def input_role(update: Update, context):
    context.user_data["role"] = update.message.text
    await update.message.reply_text("Enter the player's credit points:")
    return INPUT_CREDIT

# Input player credit
async def input_credit(update: Update, context):
    context.user_data["credit"] = float(update.message.text)
    await update.message.reply_text("Enter the player's recent points:")
    return INPUT_POINTS

# Input player points
async def input_points(update: Update, context):
    context.user_data["points"] = int(update.message.text)
    await update.message.reply_text("Enter the pitch report (e.g., batting-friendly, bowling-friendly):")
    return INPUT_PITCH

# Input pitch report
async def input_pitch(update: Update, context):
    context.user_data["pitch"] = update.message.text
    await update.message.reply_text("Enter the player's recent stats (e.g., last 5 matches):")
    return INPUT_STATS

# Input recent stats
async def input_stats(update: Update, context):
    context.user_data["stats"] = update.message.text

    # Save player data
    player = {
        "name": context.user_data["name"],
        "role": context.user_data["role"],
        "credit": context.user_data["credit"],
        "points": context.user_data["points"],
        "pitch": context.user_data["pitch"],
        "stats": context.user_data["stats"]
    }
    players.append(player)

    await update.message.reply_text(f"Player {player['name']} added successfully!")
    return ConversationHandler.END

# Make team command
async def make_team(update: Update, context):
    if not players:
        await update.message.reply_text("No players added yet. Use /addplayer to add players.")
        return

    # Define team constraints
    team_composition = {"Batsman": 3, "Bowler": 2, "All-rounder": 2, "Wicket-keeper": 1}
    total_players = 11
    total_credits = 100

    # Sort players by points (descending order)
    sorted_players = sorted(players, key=lambda x: x["points"], reverse=True)

    # Select team
    selected_team = []
    remaining_credits = total_credits
    remaining_roles = team_composition.copy()

    for player in sorted_players:
        if len(selected_team) >= total_players:
            break

        role = player["role"]
        if role in remaining_roles and player["credit"] <= remaining_credits:
            selected_team.append(player)
            remaining_credits -= player["credit"]
            remaining_roles[role] -= 1
            if remaining_roles[role] == 0:
                del remaining_roles[role]

    # Display selected team
    team_message = "Selected Team:\n"
    for player in selected_team:
        team_message += (
            f"{player['name']} ({player['role']}) - Credits: {player['credit']}, Points: {player['points']}\n"
        )
    team_message += f"Remaining Credits: {remaining_credits}"

    await update.message.reply_text(team_message)

# Cancel command
async def cancel(update: Update, context):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# Main function
def main():
    # Replace 'YOUR_TOKEN' with your bot's API token
    application = Application.builder().token("7967838214:AAHh1ExRNLaFBNC67iv400OetAXMUrIj5vE").build()

    # Conversation handler for adding players
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addplayer", add_player)],
        states={
            INPUT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_name)],
            INPUT_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_role)],
            INPUT_CREDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_credit)],
            INPUT_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_points)],
            INPUT_PITCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_pitch)],
            INPUT_STATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_stats)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("maketeam", make_team))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()