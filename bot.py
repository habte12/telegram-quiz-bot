import logging
import pandas as pd
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os
TOKEN = os.getenv("8773162240:AAFp2r0gJYxLRzVUeRFw-nwoNqUNn_JZaaw")


ADMIN_ID = 5227519306  # replace with your Telegram ID

# مراحل
NAME, SECTION, ROLL, QUIZ = range(4)

# questions
questions = [
    {"q": "What does ICT stand for?", "a": "Information and Communication Technology"},
    {"q": "What is the brain of a computer?", "a": "CPU"},
]

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📘 ICT Quiz Bot\n\n"
        "This is an ICT subject quiz bot for grade 7 and 8 students.\n"
        "Developed by Goro Primary School ICT Department.\n\n"
        "Please enter your full name:"
    )
    await update.message.reply_text(text)
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    keyboard = [["7G", "7H"], ["8F", "8G"]]
    await update.message.reply_text(
        "Choose your section:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return SECTION

async def get_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["section"] = update.message.text
    await update.message.reply_text("Enter your roll number:")
    return ROLL

async def get_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["roll"] = update.message.text
    context.user_data["score"] = 0
    context.user_data["q_index"] = 0
    context.user_data["start_time"] = time.time()

    await update.message.reply_text("⏱ Exam started! You have 10 minutes.\n\n" + questions[0]["q"])
    return QUIZ

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check time
    if time.time() - context.user_data["start_time"] > 600:
        await update.message.reply_text("⏰ Time is up!")
        return await finish(update, context)

    user_answer = update.message.text
    q_index = context.user_data["q_index"]

    if user_answer.lower() == questions[q_index]["a"].lower():
        context.user_data["score"] += 1

    q_index += 1

    if q_index >= len(questions):
        return await finish(update, context)

    context.user_data["q_index"] = q_index
    await update.message.reply_text(questions[q_index]["q"])
    return QUIZ

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data

    result = {
        "Name": data["name"],
        "Section": data["section"],
        "Roll": data["roll"],
        "Score": data["score"]
    }

    try:
        df = pd.read_excel("results.xlsx")
        df = pd.concat([df, pd.DataFrame([result])])
    except:
        df = pd.DataFrame([result])

    df.to_excel("results.xlsx", index=False)

    await update.message.reply_text(
        f"✅ Exam finished!\nScore: {data['score']}/{len(questions)}",
        reply_markup=ReplyKeyboardMarkup([["Retake Exam"]], one_time_keyboard=True)
    )

    return ConversationHandler.END

async def retake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

async def get_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        await update.message.reply_document(open("results.xlsx", "rb"))
    else:
        await update.message.reply_text("❌ You are not allowed to access results.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_section)],
            ROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_roll)],
            QUIZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz)],
        },
        fallbacks=[MessageHandler(filters.Regex("Retake Exam"), retake)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("results", get_results))

    app.run_polling()

if __name__ == "__main__":
    main()
