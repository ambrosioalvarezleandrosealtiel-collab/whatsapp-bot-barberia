from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def bot():

    incoming_msg = request.values.get("Body", "").strip().lower()
    print("MENSAJE RECIBIDO:", incoming_msg)

    resp = MessagingResponse()
    msg = resp.message()

    if "hola" in incoming_msg:
        msg.body(
            "💈 Barbería Los Reyes\n\n"
            "1️⃣ Agendar cita\n"
            "2️⃣ Ver precios\n"
            "3️⃣ Horarios"
        )

    elif incoming_msg == "1":
        msg.body(
            "✂️ Servicios disponibles:\n"
            "1 Corte\n"
            "2 Barba\n"
            "3 Corte + Barba"
        )

    elif incoming_msg == "2":
        msg.body(
            "💰 Precios:\n"
            "Corte $120\n"
            "Barba $80\n"
            "Corte + Barba $180"
        )

    else:
        msg.body("Escribe *hola* para iniciar.")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
