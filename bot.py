import logging
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

TOKEN = "8339346626:AAEF-MdMG4KQ6ZIitD8XbwbT7OJlAlRlF0k"

RIVAL, FECHA, HORA, LUGAR = range(4)

CONVOCADAS = [
    "Carla", "Keyla", "Laia", "Lucia", "Luna",
    "Marta", "Paula", "Sara", "Sofia",
    "Valentina", "Vera"
]

partido_data = {}
mensaje_convocatoria_id = None
chat_id_global = None


# ---------------- CONVERSACIÓN ----------------

async def convocatoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¿Contra quién se juega?")
    return RIVAL


async def rival(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partido_data["rival"] = update.message.text
    await update.message.reply_text("¿Fecha del partido? (Ej: Domingo 22/2)")
    return FECHA


async def fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partido_data["fecha"] = update.message.text
    await update.message.reply_text("¿Hora del partido? (Ej: 11:30)")
    return HORA


async def hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partido_data["hora"] = update.message.text
    await update.message.reply_text("¿Lugar del partido?")
    return LUGAR


async def lugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mensaje_convocatoria_id, chat_id_global

    partido_data["lugar"] = update.message.text
    partido_data["estado"] = {} # guardamos estado individual

    texto = generar_convocatoria()

    mensaje = await update.message.reply_text(texto)

    mensaje_convocatoria_id = mensaje.message_id
    chat_id_global = mensaje.chat_id

    return ConversationHandler.END


# ---------------- GENERAR TEXTO ----------------

def generar_convocatoria():

    total = len(CONVOCADAS)
    confirmadas = sum(1 for estado in partido_data["estado"].values() if estado == "✅")

    lista = ""
    for jugadora in CONVOCADAS:
        estado = partido_data["estado"].get(jugadora, "")
        if estado:
            lista += f"{jugadora} {estado}\n"
        else:
            lista += f"{jugadora}\n"

    texto = (
        "❗CONVOCATORIA❗\n\n"
        f"🆚 {partido_data['rival']}\n"
        f"🏟️ {partido_data['lugar']}\n"
        "🏆 Partido de Liga\n"
        f"🗓️ {partido_data['fecha']}\n"
        f"🕓 {partido_data['hora']} Zona gradas.\n"
        "🩳 Ropa del club\n"
        "🛀 Ducha obligatoria\n"
        "⏰ Se ruega puntualidad\n\n"
        "*CONVOCADAS*\n"
        f"{lista}\n"
        f"📊 {confirmadas}/{total} confirmadas\n\n"
        "Escribir:\n"
        "Nombre + ✅ o Nombre + ok\n"
        "Nombre + no"
    )

    return texto


# ---------------- CONFIRMACIONES ----------------

async def gestionar_respuesta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mensaje_convocatoria_id

    if not mensaje_convocatoria_id:
        return

    texto = update.message.text.strip().lower()

    patron = r"^([a-záéíóúñ]+)\s*(✅|ok|no)$"
    match = re.match(patron, texto)

    if not match:
        return

    nombre_escrito = match.group(1)
    accion = match.group(2)

    nombre_real = None
    for jugadora in CONVOCADAS:
        if jugadora.lower() == nombre_escrito:
            nombre_real = jugadora
            break

    if not nombre_real:
        return

    if accion in ["✅", "ok"]:
        partido_data["estado"][nombre_real] = "✅"

    elif accion == "no":
        partido_data["estado"][nombre_real] = "❌"

    nuevo_texto = generar_convocatoria()

    await context.bot.edit_message_text(
        chat_id=chat_id_global,
        message_id=mensaje_convocatoria_id,
        text=nuevo_texto
    )

    await update.message.delete()


# ---------------- MAIN ----------------

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("convocatoria", convocatoria)],
        states={
            RIVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, rival)],
            FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fecha)],
            HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hora)],
            LUGAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, lugar)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gestionar_respuesta))

    app.run_polling()


if __name__ == "__main__":
    main()