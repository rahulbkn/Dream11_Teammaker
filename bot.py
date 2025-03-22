import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
INPUT_URL = 0

# Start command
async def start(update: Update, context):
    await update.message.reply_text(
        "Welcome to the Dream11 Team Maker Bot!\n\n"
        "Use /scrape to fetch player stats and pitch report from a website.\n"
        "Use /maketeam to generate a team."
    )

# Scrape command
async def scrape(update: Update, context):
    await update.message.reply_text("Please enter the URL of the match page on ESPN Cricinfo:")
    return INPUT_URL

# Input URL and scrape data
async def input_url(update: Update, context):
    url = update.message.text

    # Scrape player stats
    player_stats = scrape_player_stats(url)
    if not player_stats:
        await update.message.reply_text("Failed to scrape player stats. Please check the URL.")
        return ConversationHandler.END

    # Scrape pitch report
    pitch_report = scrape_pitch_report(url)
    if not pitch_report:
        await update.message.reply_text("Failed to scrape pitch report. Please check the URL.")
        return ConversationHandler.END

    # Store data in context
    context.user_data["player_stats"] = player_stats
    context.user_data["pitch_report"] = pitch_report

    # Display scraped data
    await update.message.reply_text(f"Player Stats:\n{pd.DataFrame(player_stats)}")
    await update.message.reply_text(f"Pitch Report:\n{pitch_report}")

    await update.message.reply_text("Data scraped successfully! Use /maketeam to generate a team.")
    return ConversationHandler.END

# Function to scrape player stats
def scrape_player_stats(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        player_stats = []
        for row in soup.select('table.batsman tbody tr'):
            columns = row.find_all('td')
            if len(columns) > 1:
                player_name = columns[0].text.strip()
                runs = columns[2].text.strip()
                balls = columns[3].text.strip()
                fours = columns[5].text.strip()
                sixes = columns[6].text.strip()
                strike_rate = columns[7].text.strip()

                # Handle missing or invalid data
                try:
                    runs = int(runs)
                    balls = int(balls)
                except ValueError:
                    continue  # Skip players with invalid data

                player_stats.append({
                    "Player": player_name,
                    "Runs": runs,
                    "Balls": balls,
                    "Fours": fours,
                    "Sixes": sixes,
                    "Strike Rate": strike_rate
                })

        return player_stats
    except Exception as e:
        logger.error(f"Error scraping player stats: {e}")
        return None

# Function to scrape pitch report
def scrape_pitch_report(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        pitch_report = soup.find('div', class_='match-info').text.strip()
        return pitch_report
    except Exception as e:
        logger.error(f"Error scraping pitch report: {e}")
        return None

# Make team command
async def make_team(update: Update, context):
    if "player_stats" not in context.user_data or "pitch_report" not in context.user_data:
        await update.message.reply_text("No data available. Use /scrape to fetch player stats and pitch report.")
        return

    player_stats = context.user_data["player_stats"]
    pitch_report = context.user_data["pitch_report"]

    # Generate team
    team_composition = {"Batsman": 3, "Bowler": 2, "All-rounder": 2, "Wicket-keeper": 1}
    total_players = 11
    total_credits = 100

    # Filter players based on pitch report
    if "batting-friendly" in pitch_report.lower():
        # Prioritize batsmen and all-rounders
        filtered_players = [player for player in player_stats if player["Runs"] > 30]
    else:
        # Prioritize bowlers
        filtered_players = [player for player in player_stats if player["Balls"] > 12]

    # Sort players by strike rate (descending order)
    sorted_players = sorted(filtered_players, key=lambda x: float(x["Strike Rate"]), reverse=True)

    # Select top 11 players
    selected_team = sorted_players[:11]

    # Display selected team
    team_message = "Selected Team:\n"
    for player in selected_team:
        team_message += (
            f"{player['Player']} - Runs: {player['Runs']}, Balls: {player['Balls']}, "
            f"Fours: {player['Fours']}, Sixes: {player['Sixes']}, Strike Rate: {player['Strike Rate']}\n"
        )
    team_message += f"Remaining Credits: {total_credits}"

    await update.message.reply_text(team_message)

# Cancel command
async def cancel(update: Update, context):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# Main function
def main():
    # Replace 'YOUR_TOKEN' with your bot's API token
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for scraping data
    scrape_handler = ConversationHandler(
        entry_points=[CommandHandler("scrape", scrape)],
        states={
            INPUT_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(scrape_handler)
    application.add_handler(CommandHandler("maketeam", make_team))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()