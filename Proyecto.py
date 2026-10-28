import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import json
import os
import shutil

import Funcionamiento

#  
ARCHIVO_CONFIG = "configuracion.json"
ARCHIVO_BAK = "configuracion.bak"
ARCHIVO_TMP = "configuracion.tmp"

# inicia programa
ventana = tk.Tk()
ventana.title("Laboratorio 2 - Agenda de Contactos con Acceso Aleatorio")
ventana.geometry("750x520")
ventana.configure(bg="#F4F6F9")


# persistencia 

def guardar_datos_json(diccionario_configuracion):
    try:
        if os.path.exists(ARCHIVO_CONFIG):
            shutil.copy(ARCHIVO_CONFIG, ARCHIVO_BAK)
        
        with open(ARCHIVO_TMP, "w", encoding="utf-8") as archivo:
            json.dump(diccionario_configuracion, archivo, indent=4)
        
        os.replace(ARCHIVO_TMP, ARCHIVO_CONFIG)
        return True 
    except PermissionError:
        messagebox.showerror("Error", "Permisos insuficientes para guardar la configuración.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Fallo al guardar configuración:\n{e}")
        return False

def leer_datos_json():
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except (json.JSONDecodeError, PermissionError, Exception):
            return {}
    return {}

def aplicar_configuracion_a_ventana(ventana_principal, titulo_label, subtitulo_label, foto_label, mensaje_label):
    config = leer_datos_json()
    if not config: 
        return 
    
    tema = config.get("tema", "Claro")
    color_letra = config.get("color_letra", "#2C3E50")
    tamano_fuente = str(config.get("tamano_fuente", "14"))
    ruta_foto = config.get("foto_perfil", "")
    nombre_usr = config.get("nombre_usuario", "")
    
    if not tamano_fuente.isdigit(): 
        tamano_fuente = "14"

    color_fondo = "#212F3D" if tema == "Oscuro" else "#F4F6F9"
    if not color_letra:
        color_letra = "white" if tema == "Oscuro" else "#2C3E50"

    ventana_principal.config(bg=color_fondo)
    titulo_label.config(bg=color_fondo, fg=color_letra, font=("Helvetica", int(tamano_fuente) + 8, "bold"))
    
    texto_sub = f"Agenda de Contactos con Acceso Aleatorio\nUsuario: {nombre_usr}" if nombre_usr else "Agenda de Contactos con Acceso Aleatorio"
    subtitulo_label.config(text=texto_sub, bg=color_fondo, fg=color_letra, font=("Helvetica", int(tamano_fuente)))
    mensaje_label.config(bg=color_fondo, fg=color_letra, font=("Helvetica", max(10, int(tamano_fuente) - 2)))

    foto_label.config(bg=color_fondo)
    if ruta_foto and os.path.exists(ruta_foto):
        try:
            imagen_original = tk.PhotoImage(file=ruta_foto)
            imagen_reducida = imagen_original.subsample(2, 2)
            foto_label.config(image=imagen_reducida)
            foto_label.image = imagen_reducida
        except Exception:
            pass


# gestion de contactos 

def abrir_ventana_contactos():
    ven_contactos = tk.Toplevel(ventana)
    ven_contactos.title("Gestión de Contactos - Acceso Aleatorio")
    ven_contactos.geometry("530x480")
    ven_contactos.resizable(False, False)
    ven_contactos.configure(bg="#FFFFFF")

    var_id = tk.StringVar()
    var_nombre = tk.StringVar()
    var_telefono = tk.StringVar()
    var_correo = tk.StringVar()
    var_ciudad = tk.StringVar()
    var_estado_posicion = tk.StringVar(value=f"Posición (tell): --- | Tamaño fijo: {Funcionamiento.TAMAÑO_REGISTRO} bytes")

    tk.Label(ven_contactos, text="Registro de Contactos", font=("Helvetica", 15, "bold"), bg="#FFFFFF", fg="#2C3E50").pack(pady=15)

    frame_form = tk.Frame(ven_contactos, bg="#FFFFFF")
    frame_form.pack(pady=5, padx=20, fill="x")

    campos = [
        ("ID (Entero único):", var_id),
        ("Nombre (máx 30):", var_nombre),
        ("Teléfono (máx 15):", var_telefono),
        ("Correo (máx 25):", var_correo),
        ("Ciudad (máx 20):", var_ciudad)
    ]

    for fila, (texto, variable) in enumerate(campos):
        tk.Label(frame_form, text=texto, bg="#FFFFFF", font=("Helvetica", 10, "bold"), anchor="w").grid(row=fila, column=0, sticky="w", pady=8)
        tk.Entry(frame_form, textvariable=variable, width=32, relief="solid", bd=1, font=("Helvetica", 10)).grid(row=fila, column=1, pady=8, padx=10)

    lbl_info_acceso = tk.Label(ven_contactos, textvariable=var_estado_posicion, bg="#EBF5FB", fg="#1B4F72", font=("Consolas", 9), relief="groove", padx=10, pady=6)
    lbl_info_acceso.pack(pady=15, fill="x", padx=25)

    def limpiar_campos():
        var_id.set("")
        var_nombre.set("")
        var_telefono.set("")
        var_correo.set("")
        var_ciudad.set("")
        var_estado_posicion.set(f"Posición (tell): --- | Tamaño fijo: {Funcionamiento.TAMAÑO_REGISTRO} bytes")

    def accion_agregar():
        id_txt = var_id.get().strip()
        if not id_txt.isdigit():
            messagebox.showwarning("Validación", "El ID debe ser un número entero.")
            return
        if not var_nombre.get().strip():
            messagebox.showwarning("Validación", "El nombre es obligatorio.")
            return

        exito, msg = Funcionamiento.agregar_contacto(
            int(id_txt), var_nombre.get().strip(), var_telefono.get().strip(), var_correo.get().strip(), var_ciudad.get().strip()
        )
        if exito:
            messagebox.showinfo("Contacto Agregado", msg)
            limpiar_campos()
        else:
            messagebox.showerror("Error", msg)

    def accion_buscar():
        id_txt = var_id.get().strip()
        if not id_txt.isdigit():
            messagebox.showwarning("Validación", "Ingresa un ID numérico para buscar.")
            return

        contacto, msg = Funcionamiento.buscar_contacto(int(id_txt))
        if contacto:
            var_nombre.set(contacto["nombre"])
            var_telefono.set(contacto["telefono"])
            var_correo.set(contacto["correo"])
            var_ciudad.set(contacto["ciudad"])
            pos = contacto["posicion_lectura"]
            num_reg = contacto["numero_registro"]
            var_estado_posicion.set(f"Registro #{num_reg} | Byte exacto (seek/tell): {pos}")
            messagebox.showinfo("Contacto Encontrado", f"{msg}\n\nRegistro #{num_reg} leído en el byte {pos}.")
        else:
            messagebox.showwarning("Búsqueda", msg)

    def accion_modificar():
        id_txt = var_id.get().strip()
        if not id_txt.isdigit():
            messagebox.showwarning("Validación", "Ingresa un ID numérico válido para modificar.")
            return

        exito, msg = Funcionamiento.modificar_contacto(
            int(id_txt), var_nombre.get().strip(), var_telefono.get().strip(), var_correo.get().strip(), var_ciudad.get().strip()
        )
        if exito:
            messagebox.showinfo("Modificación En El Lugar", msg)
        else:
            messagebox.showerror("Error", msg)

    frame_botones = tk.Frame(ven_contactos, bg="#FFFFFF")
    frame_botones.pack(pady=15)

    tk.Button(frame_botones, text="Agregar", width=11, bg="#27AE60", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=accion_agregar).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Buscar por ID", width=12, bg="#2980B9", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=accion_buscar).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Modificar", width=11, bg="#F39C12", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=accion_modificar).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Limpiar", width=9, bg="#95A5A6", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=limpiar_campos).pack(side="left", padx=5)


# funciones de menu 

def accion_exportar_json():
    exito, msg = Funcionamiento.exportar_a_json()
    if exito:
        messagebox.showinfo("Exportar a JSON", msg)
    else:
        messagebox.showwarning("Exportar a JSON", msg)

def accion_exportar_pdf():
    exito, msg = Funcionamiento.generar_reporte_pdf()
    if exito:
        messagebox.showinfo("Generar Reporte PDF", msg)
    else:
        messagebox.showerror("Error en Reporte PDF", msg)

def accion_verificar_integridad():
    exito, msg = Funcionamiento.verificar_integridad()
    if exito:
        messagebox.showinfo("Verificación SHA-256", msg)
    else:
        messagebox.showwarning("Alerta de Integridad", msg)

def accion_crear_respaldo_zip():
    exito, msg = Funcionamiento.crear_respaldo_zip()
    if exito:
        messagebox.showinfo("Respaldo ZIP Creado", msg)
    else:
        messagebox.showwarning("Respaldo ZIP", msg)

def accion_info_archivo():
    info = Funcionamiento.obtener_info_archivo()
    messagebox.showinfo("Información y Metadatos del Archivo", info)

def accion_ayuda():
    messagebox.showinfo(
        "Ayuda del Sistema",
        "Agenda de Contactos con Acceso Aleatorio\n"
        "Universidad Rafael Landívar\n\n"
        "• Estructura de registro: 100 bytes fijos (ID:10, Nombre:30, Tel:15, Correo:25, Ciudad:20).\n"
        "• Acceso directo mediante índice primario (indice.json) + seek() y tell().\n"
        "• Seguridad mediante hash SHA-256 y respaldos comprimidos en formato ZIP."
    )


# seting programa 1 

def abrir_settings():
    ventana_settings = tk.Toplevel(ventana)
    ventana_settings.title("Configuración de Interfaz")
    ventana_settings.geometry("450x560")
    ventana_settings.resizable(False, False)
    ventana_settings.configure(bg="#FFFFFF")

    var_nombre = tk.StringVar()
    var_tema = tk.StringVar(value="Claro")
    var_idioma = tk.StringVar(value="Español")
    var_fuente = tk.StringVar(value="14")
    var_color_barra = tk.StringVar()
    var_color_letra = tk.StringVar()
    var_ruta_foto = tk.StringVar()

    def seleccionar_color_letra():
        color = colorchooser.askcolor(title="Color de letra")[1]
        if color: var_color_letra.set(color)

    def seleccionar_foto():
        ruta = filedialog.askopenfilename(title="Seleccionar foto", filetypes=[("Imágenes PNG", "*.png")])
        if ruta: var_ruta_foto.set(ruta)

    def accion_guardar():
        configuracion = {
            "nombre_usuario": var_nombre.get(),
            "tema": var_tema.get(),
            "idioma": var_idioma.get(),
            "tamano_fuente": var_fuente.get(),
            "color_barra": var_color_barra.get(),
            "color_letra": var_color_letra.get(),
            "foto_perfil": var_ruta_foto.get()
        }
        if guardar_datos_json(configuracion):
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
            aplicar_configuracion_a_ventana(ventana, titulo_principal, subtitulo, label_foto, mensaje)
            ventana_settings.destroy()

    config = leer_datos_json()
    if config:
        var_nombre.set(config.get("nombre_usuario", ""))
        var_tema.set(config.get("tema", "Claro"))
        var_idioma.set(config.get("idioma", "Español"))
        var_fuente.set(config.get("tamano_fuente", "14"))
        var_color_letra.set(config.get("color_letra", ""))
        var_ruta_foto.set(config.get("foto_perfil", ""))

    tk.Label(ventana_settings, text="Preferencias de Usuario", font=("Helvetica", 16, "bold"), bg="#FFFFFF", fg="#2C3E50").pack(pady=15)
    tk.Label(ventana_settings, text="Nombre de usuario:", bg="#FFFFFF", font=("Helvetica", 10)).pack()
    tk.Entry(ventana_settings, textvariable=var_nombre, width=35, relief="solid", bd=1).pack(pady=5)
    
    tk.Label(ventana_settings, text="Tema de interfaz:", bg="#FFFFFF", font=("Helvetica", 10)).pack(pady=(12, 5))
    opciones_tema = tk.Frame(ventana_settings, bg="#FFFFFF")
    opciones_tema.pack()
    tk.Radiobutton(opciones_tema, text="Claro", variable=var_tema, value="Claro", bg="#FFFFFF").pack(side="left", padx=10)
    tk.Radiobutton(opciones_tema, text="Oscuro", variable=var_tema, value="Oscuro", bg="#FFFFFF").pack(side="left", padx=10)
    
    tk.Label(ventana_settings, text="Tamaño de fuente:", bg="#FFFFFF", font=("Helvetica", 10)).pack(pady=(12, 5))
    tk.Entry(ventana_settings, textvariable=var_fuente, width=10, relief="solid", bd=1).pack()
    
    tk.Label(ventana_settings, text="Color de texto:", bg="#FFFFFF", font=("Helvetica", 10)).pack(pady=(12, 5))
    tk.Button(ventana_settings, text="Seleccionar Color de Letra", command=seleccionar_color_letra, relief="groove", bg="#ECF0F1").pack(pady=5)
    
    tk.Label(ventana_settings, text="Foto de perfil (.png):", bg="#FFFFFF", font=("Helvetica", 10)).pack(pady=(12, 5))
    tk.Button(ventana_settings, text="Explorar archivos...", command=seleccionar_foto, relief="groove", bg="#ECF0F1").pack()
    
    tk.Button(ventana_settings, text="Guardar Configuración", width=25, bg="#2980B9", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=accion_guardar).pack(pady=25)


# menu principal 

barra_menu = tk.Menu(ventana)

# Menú Contactos
menu_contactos = tk.Menu(barra_menu, tearoff=0)
menu_contactos.add_command(label="Agregar / Buscar / Modificar", command=abrir_ventana_contactos)
menu_contactos.add_separator()
menu_contactos.add_command(label="Salir", command=ventana.quit)
barra_menu.add_cascade(label="Contactos", menu=menu_contactos)

# Menú Exportar
menu_exportar = tk.Menu(barra_menu, tearoff=0)
menu_exportar.add_command(label="Exportar a JSON", command=accion_exportar_json)
menu_exportar.add_command(label="Generar reporte PDF", command=accion_exportar_pdf)
barra_menu.add_cascade(label="Exportar", menu=menu_exportar)

# Menú Herramientas
menu_herramientas = tk.Menu(barra_menu, tearoff=0)
menu_herramientas.add_command(label="Verificar integridad (SHA-256)", command=accion_verificar_integridad)
menu_herramientas.add_command(label="Crear respaldo ZIP", command=accion_crear_respaldo_zip)
menu_herramientas.add_separator()
menu_herramientas.add_command(label="Información del archivo", command=accion_info_archivo)
barra_menu.add_cascade(label="Herramientas", menu=menu_herramientas)

# Menú Ayuda
menu_ayuda = tk.Menu(barra_menu, tearoff=0)
menu_ayuda.add_command(label="Acerca de...", command=accion_ayuda)
menu_ayuda.add_separator()
menu_ayuda.add_command(label="Preferencias Visuales (Settings)", command=abrir_settings)
barra_menu.add_cascade(label="Ayuda", menu=menu_ayuda)

ventana.config(menu=barra_menu)


# ventana pr9incipal 

titulo_principal = tk.Label(ventana, text="Laboratorio 2 - Manejo de Archivos", font=("Helvetica", 22, "bold"), bg="#F4F6F9", fg="#2C3E50")
titulo_principal.pack(pady=(50, 10))

subtitulo = tk.Label(ventana, text="Agenda de Contactos con Acceso Aleatorio", font=("Helvetica", 14), bg="#F4F6F9", fg="#34495E")
subtitulo.pack()

label_foto = tk.Label(ventana, bg="#F4F6F9")
label_foto.pack(pady=15)

btn_acceso_rapido = tk.Button(
    ventana, text="Administrar Contactos", font=("Helvetica", 12, "bold"),
    bg="#2980B9", fg="white", padx=20, pady=8, relief="flat", command=abrir_ventana_contactos
)
btn_acceso_rapido.pack(pady=15)

mensaje = tk.Label(
    ventana,
    text="Usa los menús superiores para gestionar contactos, exportar reportes o verificar la integridad del archivo.",
    font=("Helvetica", 10), bg="#F4F6F9", fg="#7F8C8D"
)
mensaje.pack(pady=20)

# aplciar estulos 
aplicar_configuracion_a_ventana(ventana, titulo_principal, subtitulo, label_foto, mensaje)

# 2. sha 
integridad_ok, mensaje_integridad = Funcionamiento.verificar_integridad()
if not integridad_ok:
    messagebox.showwarning("Alerta de Seguridad al Iniciar", mensaje_integridad)

ventana.mainloop()