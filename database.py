from supabase_client import supabase

TABLE = "citas"

def crear_cita(telefono, cliente, servicio, fecha, hora):
    data = {"telefono": telefono, "cliente": cliente,
            "servicio": servicio, "fecha": fecha, "hora": hora}
    res = supabase.table(TABLE).insert(data).execute()
    return res.data[0] if res.data else None

def obtener_cita(telefono):
    res = supabase.table(TABLE).select("*").eq("telefono", telefono).limit(1).execute()
    return res.data[0] if res.data else None

def cancelar_cita(telefono):
    supabase.table(TABLE).delete().eq("telefono", telefono).execute()

def actualizar_hora_cita(telefono, nueva_hora):
    res = supabase.table(TABLE).update({"hora": nueva_hora}).eq("telefono", telefono).execute()
    return res.data[0] if res.data else None

def obtener_horas_ocupadas(fecha):
    res = supabase.table(TABLE).select("hora").eq("fecha", fecha).execute()
    return [row["hora"] for row in res.data] if res.data else []
