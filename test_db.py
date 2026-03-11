from supabase_client import supabase

print("Probando conexion...")

# Insertar
res = supabase.table("citas").insert({
    "telefono": "+521234567890",
    "cliente":  "+521234567890",
    "servicio": "Corte",
    "fecha":    "2026-03-10",
    "hora":     "3:00 PM"
}).execute()
print("Insercion OK:", res.data)

# Leer
res2 = supabase.table("citas").select("*").execute()
print("Registros:", res2.data)

# Limpiar
supabase.table("citas").delete().eq("telefono", "+521234567890").execute()
print("Registro de prueba eliminado. Todo funciona!")
