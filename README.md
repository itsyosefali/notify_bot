# Exam Notification Bot

A Telegram bot that helps you manage and get reminded about upcoming exams.

## Features

- ✅ Add exams with date, title, and description
- ✅ List all upcoming exams (personal and group)
- ✅ Automatic reminders 1 day before exams
- ✅ Per-user and per-group data isolation
- ✅ Remove exams by ID
- ✅ Works in both private chats and groups

## Setup

1. **Get a Telegram Bot Token**
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Copy the token

2. **Set up RDS Database (PostgreSQL)**
   - Create an RDS PostgreSQL instance on AWS
   - Note the endpoint, port, username, and password
   - Create a database named `examdb` (or your preferred name)

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the Bot**
   ```bash
   python setup.py
   ```
   Then edit `.env` file with your configuration:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   DATABASE_URL=postgresql://username:password@your-rds-endpoint.amazonaws.com:5432/examdb
   ```

5. **Run the Bot**
   ```bash
   python bot.py
   ```

## Usage

### Commands

- `/start` - Welcome message and help
- `/help` - Show all available commands
- `/add_exam YYYY-MM-DD Title Description` - Add a new exam
- `/list_exams` - List all upcoming exams
- `/remove_exam <id>` - Remove an exam by ID

### Examples

```
/add_exam 2024-03-15 Math Final Exam Important calculus test
/list_exams
/remove_exam 1
```

## Data Isolation

- **Personal Exams**: Created in private chats, only visible to you
- **Group Exams**: Created in group chats, visible to all group members
- Each user can only remove their own exams

## Notifications

The bot automatically sends reminders at 9:00 AM daily for exams happening the next day.

## Database

The bot uses SQLite database (`exams.db`) to store exam data. The database is created automatically on first run.
