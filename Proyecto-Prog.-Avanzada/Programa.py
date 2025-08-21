import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

#------Conexion a Base de datos Mysql------#
db = mysql.connector.connect(
    host="localhost", user="root", password="Lennon25@", database="violet_app"
)
cursor = db.cursor(dictionary=True)

#------Utlidades-----
def run_query(query, params=(), fetch=False):
    cursor.execute(query, params)
    if fetch:
        return cursor.fetchall()
    db.commit()


def sel_id(listbox):
    sel = listbox.curselection()
    return listbox.get(sel[0]).split(" - ")[0] if sel else None

# --- DOLLS ---
def listar_dolls():
    listbox_dolls.delete(0, tk.END)
    for d in run_query("SELECT * FROM AutoMemoryDoll", fetch=True):
        listbox_dolls.insert(tk.END, f"{d['id_doll']} - {d['nombre']} ({d['edad']} años) [{d['estado']}] - {d['cartas_en_proceso']}")

def crear_doll():
    n, e = entry_doll_nombre.get().strip(), entry_doll_edad.get().strip()
    if not n or not e.isdigit(): return messagebox.showerror("Error", "Nombre y edad válidos")
    run_query("INSERT INTO AutoMemoryDoll (nombre,edad,estado,cartas_en_proceso) VALUES (%s,%s,'activo',0)", (n,int(e)))
    listar_dolls()

def eliminar_doll():
    id = sel_id(listbox_dolls)
    if id: run_query("DELETE FROM AutoMemoryDoll WHERE id_doll=%s",(id,)); listar_dolls()

# --- CLIENTES ---
def listar_clientes(filtro=""):
    listbox_clientes.delete(0, tk.END)
    q = "SELECT * FROM Cliente WHERE nombre LIKE %s OR ciudad LIKE %s" if filtro else "SELECT * FROM Cliente"
    for c in run_query(q, (f"%{filtro}%",f"%{filtro}%") if filtro else (), fetch=True):
        listbox_clientes.insert(tk.END,f"{c['id_cliente']} - {c['nombre']} - {c['ciudad']}")

def crear_cliente():
    n,c,m,ct = entry_cliente_nombre.get().strip(), entry_cliente_ciudad.get().strip(), entry_cliente_motivo.get().strip(), entry_cliente_contacto.get().strip()
    if not n or not c: return messagebox.showerror("Error", "Nombre y ciudad obligatorios")
    run_query("INSERT INTO Cliente (nombre,ciudad,motivo_carta,contacto) VALUES (%s,%s,%s,%s)",(n,c,m,ct))
    listar_clientes()

def editar_cliente():
    id = sel_id(listbox_clientes)
    if not id: return
    run_query("UPDATE Cliente SET nombre=%s,ciudad=%s,motivo_carta=%s,contacto=%s WHERE id_cliente=%s",
              (entry_cliente_nombre.get(), entry_cliente_ciudad.get(), entry_cliente_motivo.get(), entry_cliente_contacto.get(), id))
    listar_clientes()

def eliminar_cliente():
    id = sel_id(listbox_clientes)
    if id: run_query("DELETE FROM Cliente WHERE id_cliente=%s",(id,)); listar_clientes()

# --- CARTAS ---
def listar_cartas():
    listbox_cartas.delete(0, tk.END)
    for r in run_query("SELECT c.id_carta,c.estado,cli.nombre cliente,d.nombre doll FROM Carta c JOIN Cliente cli ON c.id_cliente=cli.id_cliente JOIN AutoMemoryDoll d ON c.id_doll=d.id_doll", fetch=True):
        listbox_cartas.insert(tk.END,f"{r['id_carta']} - {r['cliente']} - Doll:{r['doll']} - {r['estado']}")

def asignar_doll():
    rows = run_query("SELECT * FROM AutoMemoryDoll WHERE estado='activo' AND cartas_en_proceso<5 ORDER BY cartas_en_proceso LIMIT 1", fetch=True)
    return rows[0] if rows else None

def crear_carta():
    id_cli = sel_id(listbox_clientes)
    if not id_cli: return messagebox.showerror("Error","Seleccione un cliente")
    doll = asignar_doll()
    if not doll: return messagebox.showerror("Error","No hay Dolls disponibles")
    run_query("INSERT INTO Carta (id_cliente,id_doll,fecha,estado,contenido) VALUES (%s,%s,NOW(),'borrador',%s)",
              (id_cli,doll['id_doll'], entry_carta_contenido.get("1.0",tk.END).strip()))
    listar_cartas()

def cambiar_estado_carta():
    id_carta = sel_id(listbox_cartas)
    if not id_carta: return
    carta = run_query("SELECT * FROM Carta WHERE id_carta=%s",(id_carta,),fetch=True)[0]
    if carta["estado"]=="borrador":
        run_query("UPDATE Carta SET estado='revisado' WHERE id_carta=%s",(id_carta,))
        run_query("UPDATE AutoMemoryDoll SET cartas_en_proceso=cartas_en_proceso+1 WHERE id_doll=%s",(carta['id_doll'],))
    elif carta["estado"]=="revisado":
        run_query("UPDATE Carta SET estado='enviado' WHERE id_carta=%s",(id_carta,))
        run_query("UPDATE AutoMemoryDoll SET cartas_en_proceso=GREATEST(cartas_en_proceso-1,0) WHERE id_doll=%s",(carta['id_doll'],))
    listar_cartas(); listar_dolls()

def eliminar_carta():
    id_carta = sel_id(listbox_cartas)
    if id_carta: run_query("DELETE FROM Carta WHERE id_carta=%s AND estado='borrador'",(id_carta,)); listar_cartas()

# --- UI ---
root = tk.Tk()
root.title("Auto Memory Dolls")
root.geometry("900x600")

tabs = ttk.Notebook(root)
tabs.pack(fill="both", expand=True)

# ============================================================
# --- TAB DOLLS ---
# ============================================================
f1 = ttk.Frame(tabs, padding=10)
tabs.add(f1, text="Dolls")

ttk.Label(f1, text="Nombre:").grid(row=0, column=0, sticky="w", pady=5)
entry_doll_nombre = ttk.Entry(f1)
entry_doll_nombre.grid(row=0, column=1, sticky="w", pady=5)

ttk.Label(f1, text="Edad:").grid(row=1, column=0, sticky="w", pady=5)
entry_doll_edad = ttk.Entry(f1)
entry_doll_edad.grid(row=1, column=1, sticky="w", pady=5)

ttk.Button(f1, text="Crear", command=crear_doll).grid(row=2, column=0, pady=5, sticky="w")
ttk.Button(f1, text="Eliminar", command=eliminar_doll).grid(row=2, column=1, pady=5, sticky="w")

listbox_dolls = tk.Listbox(f1, height=10)
listbox_dolls.grid(row=3, column=0, columnspan=2, sticky="we", pady=5)

# ============================================================
# --- TAB CLIENTES ---
# ============================================================
f2 = ttk.Frame(tabs, padding=10)
tabs.add(f2, text="Clientes")

labels_clientes = ["Nombre", "Ciudad", "Motivo", "Contacto"]
entries_clientes = {}

for i, label in enumerate(labels_clientes):
    ttk.Label(f2, text=label + ":").grid(row=i, column=0, sticky="w", pady=5)
    entry = ttk.Entry(f2)
    entry.grid(row=i, column=1, sticky="w", pady=5)
    entries_clientes[label] = entry

entry_cliente_nombre = entries_clientes["Nombre"]
entry_cliente_ciudad = entries_clientes["Ciudad"]
entry_cliente_motivo = entries_clientes["Motivo"]
entry_cliente_contacto = entries_clientes["Contacto"]

ttk.Button(f2, text="Crear", command=crear_cliente).grid(row=4, column=0, pady=5, sticky="w")
ttk.Button(f2, text="Editar", command=editar_cliente).grid(row=4, column=1, pady=5, sticky="w")
ttk.Button(f2, text="Eliminar", command=eliminar_cliente).grid(row=4, column=2, pady=5, sticky="w")

# Busqueda
ttk.Label(f2, text="Buscar (nombre/ciudad):").grid(row=5, column=0, sticky="w", pady=5)
entry_busqueda = ttk.Entry(f2)
entry_busqueda.grid(row=5, column=1, sticky="w", pady=5)

ttk.Button(f2, text="Buscar", command=lambda: listar_clientes(entry_busqueda.get())).grid(row=6, column=0, pady=5, sticky="w")
ttk.Button(f2, text="Todos", command=lambda: listar_clientes()).grid(row=6, column=1, pady=5, sticky="w")

listbox_clientes = tk.Listbox(f2, height=10)
listbox_clientes.grid(row=7, column=0, columnspan=3, sticky="we", pady=5)

# ============================================================
# --- TAB CARTAS ---
# ============================================================
f3 = ttk.Frame(tabs, padding=10)
tabs.add(f3, text="Cartas")

ttk.Label(f3, text="Contenido:").grid(row=0, column=0, sticky="nw", pady=5)
entry_carta_contenido = tk.Text(f3, height=5, width=50)
entry_carta_contenido.grid(row=0, column=1, pady=5, sticky="w")

ttk.Button(f3, text="Crear", command=crear_carta).grid(row=1, column=0, pady=5, sticky="w")
ttk.Button(f3, text="Cambiar Estado", command=cambiar_estado_carta).grid(row=1, column=1, pady=5, sticky="w")
ttk.Button(f3, text="Eliminar", command=eliminar_carta).grid(row=1, column=2, pady=5, sticky="w")

listbox_cartas = tk.Listbox(f3, height=10)
listbox_cartas.grid(row=2, column=0, columnspan=3, sticky="we", pady=5)

# ============================================================
# Inicializar
listar_dolls()
listar_clientes()
listar_cartas()

root.mainloop()

