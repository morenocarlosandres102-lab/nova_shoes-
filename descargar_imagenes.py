
import os
import requests
from pathlib import Path
from app import conectar_db

# Carpeta donde se guardarán las fotografías
CARPETA = Path("static/img")
CARPETA.mkdir(parents=True, exist_ok=True)

conexion = conectar_db()
cursor = conexion.cursor(dictionary=True)

cursor.execute("""
    SELECT id_producto, nombre, imagen
    FROM productos
    ORDER BY id_producto
""")

productos = cursor.fetchall()

# Evita descargar varias veces la misma dirección
imagenes_descargadas = {}

for producto in productos:
    id_producto = producto["id_producto"]
    nombre = producto["nombre"]
    url = producto["imagen"]

    if not url or not url.startswith("http"):
        print(f"Sin dirección válida: {nombre}")
        continue

    try:
        if url not in imagenes_descargadas:
            respuesta = requests.get(url, timeout=30)
            respuesta.raise_for_status()

            tipo = respuesta.headers.get("Content-Type", "").lower()

            extensiones = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp"
            }

            extension = next(
                (ext for tipo_img, ext in extensiones.items()
                 if tipo.startswith(tipo_img)),
                None
            )

            if not extension:
                print(f"No es una imagen válida: {nombre}")
                continue

            imagenes_descargadas[url] = (
                respuesta.content,
                extension
            )

        contenido, extension = imagenes_descargadas[url]

        nombre_archivo = f"producto_{id_producto}{extension}"
        ruta = CARPETA / nombre_archivo

        with open(ruta, "wb") as archivo:
            archivo.write(contenido)

        cursor.execute("""
            UPDATE productos
            SET imagen = %s
            WHERE id_producto = %s
        """, (nombre_archivo, id_producto))

        print(f"Imagen guardada: {nombre}")

    except Exception as error:
        print(f"Error con {nombre}: {error}")

conexion.commit()
cursor.close()
conexion.close()

print("\nProceso terminado.")
print("Revisa la carpeta static/img.")
