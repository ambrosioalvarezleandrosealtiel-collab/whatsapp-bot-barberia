from supabase_client import supabase

def crear_cita(telefono, cliente, servicio, fecha, hora):

    data = {
        "telefono": telefono,
        "cliente": cliente,
        "servicio": servicio,
        "fecha": fecha,
        "hora": hora,
        "estado": "activa"
    }

    supabase.table("citas").insert(data).execute()


def obtener_cita(telefono):

    response = supabase.table("citas") \
        .select("*") \
        .eq("telefono", telefono) \
        .order("id", desc=True) \
        .limit(1) \
        .execute()

    if response.data:
        return response.data[0]

    return None
