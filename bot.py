from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    crear_cita,
    obtener_cita,
    cancelar_cita,
    actualizar_hora_cita,
    obtener_horas_ocupadas,
)
import datetime

app = Flask(__name__)

# ─────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────

HORARIOS_TOTALES = [
    "3:00 PM",
    "4:00 PM",
    "5:00 PM",
    "6:00 PM",
]

SERVICIOS = {
    "1": ("Corte",        "$120"),
    "2": ("Barba",        "$80"),
    "3": ("Corte + Barba","$180"),
}

# ─────────────────────────────────────────
#  ESTADO EN MEMORIA  (reemplazable por Redis)
# ─────────────────────────────────────────
usuarios_estado: dict = {}

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def horarios_disponibles() -> list[str]:
    """Devuelve los horarios que aún no están ocupados hoy."""
    ocupadas = obtener_horas_ocupadas(str(datetime.date.today()))
    return [h for h in HORARIOS_TOTALES if h not in ocupadas]


def menu_horarios(horarios: list[str]) -> str:
    if not horarios:
        return "😔 No hay horarios disponibles por hoy. Intenta mañana."
    texto = "⏰ Horarios disponibles\n\n"
    for i, h in enumerate(horarios, start=1):
        texto += f"{i}️⃣ {h}\n"
    return texto


def responder(texto: str) -> str:
    """Envuelve el texto en TwiML y lo retorna."""
    resp = MessagingResponse()
    resp.message(texto)
    return str(resp)


def set_estado(telefono: str, **kwargs) -> None:
    usuarios_estado[telefono] = kwargs


def get_estado(telefono: str) -> dict:
    return usuarios_estado.get(telefono, {})

# ─────────────────────────────────────────
#  RUTAS
# ─────────────────────────────────────────

@app.route("/")
def home():
    return "💈 Bot Barbería Los Reyes — activo"


@app.route("/bot", methods=["POST"])
def bot():
    mensaje  = request.values.get("Body", "").strip()
    telefono = request.values.get("From", "")
    msg_l    = mensaje.lower()

    estado_actual = get_estado(telefono)
    flujo         = estado_actual.get("flujo")

    # ── SALUDO / MENÚ PRINCIPAL ──────────────────────────────────────
    if msg_l in ("hola", "inicio", "menu", "menú"):
        set_estado(telefono, flujo="menu")
        return responder(
            "💈 *Barbería Los Reyes*\n\n"
            "1️⃣ Agendar cita\n"
            "2️⃣ Ver precios\n"
            "3️⃣ Horarios disponibles\n"
            "4️⃣ Mi cita\n\n"
            "_Responde con el número de tu opción._"
        )

    # ── OPCIÓN 2: PRECIOS ────────────────────────────────────────────
    if msg_l == "2" and flujo == "menu":
        return responder(
            "💲 *Lista de precios*\n\n"
            "✂️  Corte          → $120\n"
            "🪒  Barba          → $80\n"
            "💈  Corte + Barba  → $180\n\n"
            "Escribe *hola* para volver al menú."
        )

    # ── OPCIÓN 3: HORARIOS ───────────────────────────────────────────
    if msg_l == "3" and flujo == "menu":
        disponibles = horarios_disponibles()
        if not disponibles:
            return responder("😔 No quedan horarios disponibles hoy.\nEscribe *hola* para el menú.")
        texto = "⏰ *Horarios disponibles hoy*\n\n"
        texto += "\n".join(f"• {h}" for h in disponibles)
        texto += "\n\nEscribe *hola* para el menú."
        return responder(texto)

    # ── OPCIÓN 4: VER MI CITA ────────────────────────────────────────
    if msg_l == "4" and flujo == "menu":
        cita = obtener_cita(telefono)
        if not cita:
            return responder(
                "❌ No tienes citas registradas.\n\n"
                "Escribe *1* para agendar una o *hola* para el menú."
            )
        set_estado(telefono, flujo="ver_cita")
        return responder(
            f"📅 *Tu cita actual*\n\n"
            f"Servicio : {cita['servicio']}\n"
            f"Hora     : {cita['hora']}\n"
            f"Fecha    : {cita['fecha']}\n\n"
            "¿Qué deseas hacer?\n"
            "1️⃣ Cambiar hora\n"
            "2️⃣ Cancelar cita\n"
            "3️⃣ Volver al menú"
        )

    # ── FLUJO: VER CITA → ACCIONES ───────────────────────────────────
    if flujo == "ver_cita":

        if msg_l == "3":
            set_estado(telefono, flujo="menu")
            return responder("De acuerdo, escribe *hola* para ver el menú 😊")

        if msg_l == "2":
            cancelar_cita(telefono)
            set_estado(telefono, flujo="menu")
            return responder(
                "✅ Tu cita ha sido *cancelada*.\n\n"
                "Escribe *hola* cuando quieras agendar una nueva. 💈"
            )

        if msg_l == "1":
            disponibles = horarios_disponibles()
            if not disponibles:
                set_estado(telefono, flujo="menu")
                return responder("😔 No hay horarios disponibles hoy para cambiar.")
            set_estado(telefono, flujo="cambiar_hora", horarios_cache=disponibles)
            return responder(menu_horarios(disponibles))

    # ── FLUJO: CAMBIAR HORA ──────────────────────────────────────────
    if flujo == "cambiar_hora":
        horarios_cache = estado_actual.get("horarios_cache", horarios_disponibles())
        try:
            index    = int(msg_l) - 1
            nueva_hora = horarios_cache[index]
        except (ValueError, IndexError):
            return responder("❌ Número inválido. Elige una opción de la lista.")

        actualizar_hora_cita(telefono, nueva_hora)
        set_estado(telefono, flujo="menu")
        return responder(
            f"✅ *Hora actualizada*\n\n"
            f"Tu nueva hora es: *{nueva_hora}*\n\n"
            "Escribe *hola* para el menú. 💈"
        )

    # ── OPCIÓN 1: AGENDAR ────────────────────────────────────────────
    if msg_l == "1" and flujo == "menu":
        cita_existente = obtener_cita(telefono)
        if cita_existente:
            set_estado(telefono, flujo="ver_cita")
            return responder(
                "⚠️ Ya tienes una cita activa:\n\n"
                f"Servicio : {cita_existente['servicio']}\n"
                f"Hora     : {cita_existente['hora']}\n"
                f"Fecha    : {cita_existente['fecha']}\n\n"
                "1️⃣ Cambiar hora\n"
                "2️⃣ Cancelar cita\n"
                "3️⃣ Volver al menú"
            )
        set_estado(telefono, flujo="elegir_servicio")
        return responder(
            "✂️ *Selecciona el servicio*\n\n"
            "1️⃣ Corte          → $120\n"
            "2️⃣ Barba          → $80\n"
            "3️⃣ Corte + Barba  → $180"
        )

    # ── FLUJO: ELEGIR SERVICIO ───────────────────────────────────────
    if flujo == "elegir_servicio":
        if msg_l not in SERVICIOS:
            return responder("❌ Opción inválida. Responde *1*, *2* o *3*.")

        nombre_servicio, _ = SERVICIOS[msg_l]
        disponibles = horarios_disponibles()

        if not disponibles:
            set_estado(telefono, flujo="menu")
            return responder(
                "😔 No hay horarios disponibles hoy.\n"
                "Escribe *hola* para el menú."
            )

        set_estado(telefono, flujo="elegir_hora",
                   servicio=nombre_servicio,
                   horarios_cache=disponibles)
        return responder(menu_horarios(disponibles))

    # ── FLUJO: ELEGIR HORA ───────────────────────────────────────────
    if flujo == "elegir_hora":
        horarios_cache = estado_actual.get("horarios_cache", horarios_disponibles())
        servicio       = estado_actual.get("servicio", "")

        try:
            index = int(msg_l) - 1
            hora  = horarios_cache[index]
        except (ValueError, IndexError):
            return responder(
                "❌ Número inválido. Elige una opción de la lista.\n\n"
                + menu_horarios(horarios_cache)
            )

        # Verificar que la hora siga disponible (race condition)
        if hora in obtener_horas_ocupadas(str(datetime.date.today())):
            nuevos = horarios_disponibles()
            set_estado(telefono, flujo="elegir_hora",
                       servicio=servicio, horarios_cache=nuevos)
            return responder(
                "⚠️ Ese horario acaba de ser tomado. Elige otro:\n\n"
                + menu_horarios(nuevos)
            )

        fecha = str(datetime.date.today())
        crear_cita(telefono, telefono, servicio, fecha, hora)
        set_estado(telefono, flujo="menu")

        return responder(
            f"✅ *¡Cita confirmada!*\n\n"
            f"💈 Servicio : {servicio}\n"
            f"⏰ Hora     : {hora}\n"
            f"📅 Fecha    : {fecha}\n\n"
            "_¡Te esperamos! Si necesitas cambiarla escribe *hola*._"
        )

    # ── FALLBACK ─────────────────────────────────────────────────────
    return responder(
        "👋 Escribe *hola* para ver el menú de opciones."
    )


# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)