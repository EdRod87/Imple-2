import os
import json
import hashlib
import zipfile
from datetime import datetime

# Intentamos importar fpdf2 para el reporte PDF
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# ================= Constantes y Archivos =================
ARCHIVO_DATOS = "contactos.dat"
ARCHIVO_INDICE = "indice.json"
ARCHIVO_HASH = "contactos.sha256"
ARCHIVO_EXPORT_JSON = "contactos_exportados.json"
ARCHIVO_REPORTE_PDF = "reporte_contactos.pdf"
ARCHIVO_RESPALDO_ZIP = "respaldo_contactos.zip"

# Estructura del registro de tamaño fijo (Total = 100 caracteres)
LONGITUD_CAMPOS = {
    "id": 10,
    "nombre": 30,
    "telefono": 15,
    "correo": 25,
    "ciudad": 20
}
TAMAÑO_REGISTRO = sum(LONGITUD_CAMPOS.values())  # 100 bytes en ASCII/UTF-8 básico


# ================= 1. Integridad con Hash (SHA-256) =================

def calcular_sha256(ruta_archivo):
    """Calcula el hash SHA-256 de un archivo."""
    if not os.path.exists(ruta_archivo):
        return None
    sha256 = hashlib.sha256()
    try:
        with open(ruta_archivo, "rb") as f:
            for bloque in iter(lambda: f.read(4096), b""):
                sha256.update(bloque)
        return sha256.hexdigest()
    except Exception:
        return None

def actualizar_hash():
    """Calcula y guarda el hash SHA-256 actual de contactos.dat."""
    hash_actual = calcular_sha256(ARCHIVO_DATOS)
    if hash_actual:
        try:
            with open(ARCHIVO_HASH, "w", encoding="utf-8") as f:
                f.write(hash_actual)
        except Exception:
            pass

def verificar_integridad():
    """Compara el hash actual de contactos.dat con el almacenado en contactos.sha256."""
    if not os.path.exists(ARCHIVO_DATOS):
        return True, "El archivo de contactos aún no existe. Integridad inicial limpia."
    
    if not os.path.exists(ARCHIVO_HASH):
        return False, "No se encontró el archivo de verificación (contactos.sha256). El archivo pudo ser alterado."

    try:
        with open(ARCHIVO_HASH, "r", encoding="utf-8") as f:
            hash_guardado = f.read().strip()
        
        hash_actual = calcular_sha256(ARCHIVO_DATOS)
        
        if hash_actual == hash_guardado:
            return True, f"Integridad verificada correctamente.\nSHA-256:\n{hash_actual}"
        else:
            return False, (
                "¡ALERTA DE INTEGRIDAD!\n"
                "El archivo 'contactos.dat' fue modificado fuera de la aplicación.\n\n"
                f"Hash esperado: {hash_guardado[:20]}...\n"
                f"Hash actual:   {hash_actual[:20]}..."
            )
    except Exception as e:
        return False, f"Error al verificar integridad: {e}"


# ================= 2. Manejo del Índice Primario =================

def cargar_indice():
    """Carga el índice primario desde indice.json."""
    if os.path.exists(ARCHIVO_INDICE):
        try:
            with open(ARCHIVO_INDICE, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except (json.JSONDecodeError, PermissionError, Exception):
            return {}
    return {}

def guardar_indice(indice):
    """Guarda el diccionario de índice en indice.json."""
    try:
        with open(ARCHIVO_INDICE, "w", encoding="utf-8") as archivo:
            json.dump(indice, archivo, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False


# ================= 3. Registros de Tamaño Fijo y Acceso Aleatorio =================

def limpiar_ascii(texto):
    """Reemplaza tildes/ñ para asegurar que 1 caracter = 1 byte exacto en UTF-8."""
    reemplazos = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")
    return str(texto).translate(reemplazos)

def formatear_registro(contacto):
    """Rellena cada campo con espacios usando ljust() hasta cumplir 100 caracteres."""
    id_str = limpiar_ascii(contacto["id"])[:LONGITUD_CAMPOS["id"]].ljust(LONGITUD_CAMPOS["id"])
    nombre = limpiar_ascii(contacto["nombre"])[:LONGITUD_CAMPOS["nombre"]].ljust(LONGITUD_CAMPOS["nombre"])
    telefono = limpiar_ascii(contacto["telefono"])[:LONGITUD_CAMPOS["telefono"]].ljust(LONGITUD_CAMPOS["telefono"])
    correo = limpiar_ascii(contacto["correo"])[:LONGITUD_CAMPOS["correo"]].ljust(LONGITUD_CAMPOS["correo"])
    ciudad = limpiar_ascii(contacto["ciudad"])[:LONGITUD_CAMPOS["ciudad"]].ljust(LONGITUD_CAMPOS["ciudad"])
    
    return f"{id_str}{nombre}{telefono}{correo}{ciudad}"

def desempaquetar_registro(registro_str):
    """Extrae los campos de un string de 100 caracteres."""
    return {
        "id": registro_str[0:10].strip(),
        "nombre": registro_str[10:40].strip(),
        "telefono": registro_str[40:55].strip(),
        "correo": registro_str[55:80].strip(),
        "ciudad": registro_str[80:100].strip()
    }

def agregar_contacto(id_contacto, nombre, telefono, correo, ciudad):
    """Agrega un contacto al final de contactos.dat, actualiza el índice y el hash."""
    indice = cargar_indice()
    id_str = str(id_contacto)
    
    if id_str in indice:
        return False, f"El contacto con ID {id_str} ya existe."
    
    contacto = {
        "id": id_str, "nombre": nombre,
        "telefono": telefono, "correo": correo, "ciudad": ciudad
    }
    registro_texto = formatear_registro(contacto)
    
    try:
        if not os.path.exists(ARCHIVO_DATOS):
            num_registro = 0
        else:
            num_registro = os.path.getsize(ARCHIVO_DATOS) // TAMAÑO_REGISTRO

        with open(ARCHIVO_DATOS, "a", encoding="utf-8") as archivo:
            archivo.write(registro_texto)
        
        indice[id_str] = num_registro
        guardar_indice(indice)
        actualizar_hash()
        
        return True, f"Contacto guardado en el registro #{num_registro}."
    except PermissionError:
        return False, "Error: Sin permisos de escritura en contactos.dat."
    except Exception as e:
        return False, f"Error al agregar contacto: {e}"

def buscar_contacto(id_contacto):
    """Busca un contacto por ID consultando el índice y saltando con seek()."""
    indice = cargar_indice()
    id_str = str(id_contacto)
    
    if id_str not in indice:
        return None, f"El ID {id_str} no existe en el índice."
    
    if not os.path.exists(ARCHIVO_DATOS):
        return None, "El archivo contactos.dat no existe."

    num_registro = indice[id_str]
    posicion_byte = num_registro * TAMAÑO_REGISTRO
    
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            archivo.seek(posicion_byte)
            posicion_actual = archivo.tell()  # Confirmamos posición con tell()
            registro = archivo.read(TAMAÑO_REGISTRO)
            
        if not registro or len(registro) < TAMAÑO_REGISTRO:
            return None, "El registro está incompleto o corrupto."
            
        contacto = desempaquetar_registro(registro)
        contacto["posicion_lectura"] = posicion_actual
        contacto["numero_registro"] = num_registro
        return contacto, "Contacto localizado mediante acceso aleatorio."
    except PermissionError:
        return None, "Error: Sin permisos de lectura."
    except Exception as e:
        return None, f"Error al leer el contacto: {e}"

def modificar_contacto(id_contacto, nuevo_nombre, nuevo_telefono, nuevo_correo, nueva_ciudad):
    """Sobrescribe únicamente el registro correspondiente usando seek() (In-Place)."""
    indice = cargar_indice()
    id_str = str(id_contacto)
    
    if id_str not in indice:
        return False, f"No se puede modificar: El ID {id_str} no existe."
    
    if not os.path.exists(ARCHIVO_DATOS):
        return False, "El archivo de contactos no existe."

    num_registro = indice[id_str]
    posicion_byte = num_registro * TAMAÑO_REGISTRO
    
    contacto_actualizado = {
        "id": id_str, "nombre": nuevo_nombre,
        "telefono": nuevo_telefono, "correo": nuevo_correo, "ciudad": nueva_ciudad
    }
    registro_texto = formatear_registro(contacto_actualizado)
    
    try:
        with open(ARCHIVO_DATOS, "r+", encoding="utf-8") as archivo:
            archivo.seek(posicion_byte)
            pos_confirmada = archivo.tell()
            archivo.write(registro_texto)
            
        actualizar_hash()
        return True, f"Registro #{num_registro} sobrescrito en el byte {pos_confirmada}."
    except PermissionError:
        return False, "Error: Sin permisos para modificar el archivo."
    except Exception as e:
        return False, f"Error al modificar contacto: {e}"


# ================= 4. Exportación a JSON y PDF =================

def exportar_a_json():
    """Exporta todos los contactos usando el índice hacia un archivo JSON."""
    indice = cargar_indice()
    if not indice or not os.path.exists(ARCHIVO_DATOS):
        return False, "No hay contactos registrados para exportar."
    
    lista_contactos = []
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            for id_str, num_registro in indice.items():
                archivo.seek(num_registro * TAMAÑO_REGISTRO)
                registro = archivo.read(TAMAÑO_REGISTRO)
                if len(registro) == TAMAÑO_REGISTRO:
                    lista_contactos.append(desempaquetar_registro(registro))
                    
        with open(ARCHIVO_EXPORT_JSON, "w", encoding="utf-8") as f_json:
            json.dump(lista_contactos, f_json, indent=4, ensure_ascii=False)
            
        return True, f"Se exportaron {len(lista_contactos)} contactos a '{ARCHIVO_EXPORT_JSON}'."
    except Exception as e:
        return False, f"Error al exportar a JSON: {e}"

def generar_reporte_pdf():
    """Genera un reporte PDF leyendo los datos desde el JSON exportado."""
    if not FPDF_DISPONIBLE:
        return False, "La librería 'fpdf2' no está instalada.\nEjecuta en consola: pip install fpdf2"

    # Primero aseguramos que el JSON exportado esté actualizado
    exito_json, msg_json = exportar_a_json()
    if not exito_json:
        return False, msg_json

    try:
        with open(ARCHIVO_EXPORT_JSON, "r", encoding="utf-8") as f:
            contactos = json.load(f)

        pdf = FPDF()
        pdf.add_page()
        
        # Título y Fecha
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Reporte de Agenda de Contactos", ln=True, align="C")
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, f"Fecha de generacion: {fecha_actual}", ln=True, align="C")
        pdf.ln(5)

        # Encabezados de tabla
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(220, 230, 240)
        pdf.cell(15, 8, "ID", border=1, fill=True, align="C")
        pdf.cell(55, 8, "Nombre", border=1, fill=True)
        pdf.cell(30, 8, "Telefono", border=1, fill=True)
        pdf.cell(55, 8, "Correo", border=1, fill=True)
        pdf.cell(35, 8, "Ciudad", border=1, fill=True)
        pdf.ln()

        # Filas de contactos
        pdf.set_font("Helvetica", "", 9)
        for c in contactos:
            pdf.cell(15, 8, str(c["id"]), border=1, align="C")
            pdf.cell(55, 8, str(c["nombre"])[:28], border=1)
            pdf.cell(30, 8, str(c["telefono"]), border=1)
            pdf.cell(55, 8, str(c["correo"])[:28], border=1)
            pdf.cell(35, 8, str(c["ciudad"])[:18], border=1)
            pdf.ln()

        pdf.output(ARCHIVO_REPORTE_PDF)
        return True, f"Reporte generado exitosamente en '{ARCHIVO_REPORTE_PDF}'."
    except Exception as e:
        return False, f"Error al generar PDF: {e}"


# ================= 5. Respaldo Comprimido (ZIP) y Metadatos =================

def crear_respaldo_zip():
    """Comprime contactos.dat e indice.json en un ZIP y compara tamaños."""
    if not os.path.exists(ARCHIVO_DATOS) or not os.path.exists(ARCHIVO_INDICE):
        return False, "Debes tener contactos registrados antes de crear un respaldo."

    try:
        tam_original = os.path.getsize(ARCHIVO_DATOS) + os.path.getsize(ARCHIVO_INDICE)
        
        with zipfile.ZipFile(ARCHIVO_RESPALDO_ZIP, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
            archivo_zip.write(ARCHIVO_DATOS)
            archivo_zip.write(ARCHIVO_INDICE)
            
        tam_comprimido = os.path.getsize(ARCHIVO_RESPALDO_ZIP)
        ahorro = tam_original - tam_comprimido
        porcentaje = (ahorro / tam_original * 100) if tam_original > 0 else 0

        mensaje = (
            f"Respaldo '{ARCHIVO_RESPALDO_ZIP}' creado con éxito.\n\n"
            f"• Tamaño original (datos + índice): {tam_original} bytes\n"
            f"• Tamaño comprimido (ZIP): {tam_comprimido} bytes\n"
            f"• Reducción: {porcentaje:.1f}%"
        )
        return True, mensaje
    except Exception as e:
        return False, f"Error al crear respaldo ZIP: {e}"

def obtener_info_archivo():
    """Devuelve tamaño, fecha de modificación y permisos usando os.stat y os.access."""
    if not os.path.exists(ARCHIVO_DATOS):
        return "El archivo 'contactos.dat' aún no existe.\nAgrega al menos un contacto para ver sus metadatos."

    try:
        estadisticas = os.stat(ARCHIVO_DATOS)
        tamano = estadisticas.st_size
        total_registros = tamano // TAMAÑO_REGISTRO
        fecha_mod = datetime.fromtimestamp(estadisticas.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
        
        permiso_lectura = "Sí (Permitido)" if os.access(ARCHIVO_DATOS, os.R_OK) else "No (Denegado)"
        permiso_escritura = "Sí (Permitido)" if os.access(ARCHIVO_DATOS, os.W_OK) else "No (Denegado)"

        return (
            f"Archivo analizado: {ARCHIVO_DATOS}\n"
            f"----------------------------------------\n"
            f"• Tamaño total: {tamano} bytes ({total_registros} registros de {TAMAÑO_REGISTRO} bytes)\n"
            f"• Última modificación: {fecha_mod}\n"
            f"• Permiso de lectura (os.R_OK): {permiso_lectura}\n"
            f"• Permiso de escritura (os.W_OK): {permiso_escritura}"
        )
    except Exception as e:
        return f"No se pudieron obtener los metadatos: {e}"