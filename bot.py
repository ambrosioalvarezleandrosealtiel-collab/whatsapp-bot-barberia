from flask import Flask, request
from database import crear_cita, obtener_cita
import datetime

app = Flask(__name__)

# memoria temporal de usuarios
usuarios_estado = {}

horarios_disponibles = [
    "3:00 PM",
    "4:00 PM",
    "5:00 PM",
    "6:00 PM"
]

@app.route("/")
def home():
    return "Bot barberia funcionando"


@app.route("/bot", methods=["POST"])
def bot():

    mensaje = request.values.get("Body", "").lower().strip()
    telefono = request.values.get("From", "")

    print("MENSAJE:", mensaje)

    # iniciar conversación
    if mensaje == "hola":

        usuarios_estado[telefono] = {"estado": "menu"}

        return """
💈 Barbería Los Reyes

1️⃣ Agendar cita
2️⃣ Ver precios
3️⃣ Horarios
4️⃣ Mi cita
"""

    # verificar estado del usuario
    estado = usuarios_estado.get(telefono, {}).get("estado")

    # AGENDAR CITA
    if mensaje == "1":

        usuarios_estado[telefono] = {"estado": "servicio"}

        return """
✂️ Selecciona servicio

1️⃣ Corte
2️⃣ Barba
3️⃣ Corte + Barba
"""

    # seleccionar servicio
    if estado == "servicio":

        servicios = {
            "1": "Corte",
            "2": "Barba",
            "3": "Corte + Barba"
        }

        if mensaje in servicios:

            usuarios_estado[telefono] = {
                "estado": "hora",
                "servicio": servicios[mensaje]
            }

            texto = "⏰ Horarios disponibles\n\n"

            for i, h in enumerate(horarios_disponibles):
                texto += f"{i+1}️⃣ {h}\n"

            return texto

    # elegir hora
    if estado == "hora":

        try:

            index = int(mensaje) - 1
            hora = horarios_disponibles[index]

            servicio = usuarios_estado[telefono]["servicio"]
            fecha = str(datetime.date.today())
            cliente = telefono

            # evitar duplicados
            cita_existente = obtener_cita(telefono)

            if cita_existente:
                return "⚠️ Ya tienes una cita registrada."

            crear_cita(telefono, cliente, servicio, fecha, hora)

            usuarios_estado[telefono] = {"estado": "menu"}

            return f"""
✅ Cita confirmada

Servicio: {servicio}
Hora: {hora}
Fecha: {fecha}

Te esperamos 💈
"""

        except:
            return "❌ Selecciona un horario válido"

    # PRECIOS
    if mensaje == "2":

        return """
💲 Precios

Corte: $120
Barba: $80
Corte + barba: $180
"""

    # HORARIOS
    if mensaje == "3":

        texto = "⏰ Horarios disponibles\n\n"

        for h in horarios_disponibles:
            texto += f"{h}\n"

        return texto

    # VER CITA
    if mensaje == "4":

        cita = obtener_cita(telefono)

        if cita:

            return f"""
📅 Tu cita

Servicio: {cita['servicio']}
Hora: {cita['hora']}
Fecha: {cita['fecha']}

1️⃣ Cambiar hora
2️⃣ Cancelar cita
"""

        else:

            return "❌ No tienes citas registradas"

    return "Escribe *hola* para iniciar"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
