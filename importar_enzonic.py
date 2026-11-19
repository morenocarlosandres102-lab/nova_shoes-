
import pymysql
import sqlparse
from getpass import getpass
from pathlib import Path
import re

# Ruta del respaldo de MySQL Workbench
archivo_sql = Path(
    r"C:\Users\USUARIO\OneDrive\Escritorio\nova_shoes_backup.sql111.sql"
)

# Datos de conexión de Enzonic
HOST = "nova-shoes-db-m33w3x.db.enzonic.com"
PUERTO = 3306
USUARIO = "u_f8fenlfjgf.nova-shoes-db-m33w3x"
BASE_DATOS = "main"

conexion = None

try:
    if not archivo_sql.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {archivo_sql}"
        )

    print("Leyendo respaldo SQL...")
    contenido = archivo_sql.read_text(encoding="utf-8-sig")

    print("Conectando con Enzonic...")
    contrasena = getpass("Contraseña de Enzonic: ")

    conexion = pymysql.connect(
        host=HOST,
        port=PUERTO,
        user=USUARIO,
        password=contrasena,
        database=BASE_DATOS,
        ssl={},
        connect_timeout=30,
        autocommit=True
    )

    print("Conexión exitosa.")
    print("Iniciando importación...\n")

    cursor = conexion.cursor()
    sentencias = sqlparse.split(contenido)

    total = 0

    for sentencia in sentencias:
        sentencia = sentencia.strip()

        if not sentencia:
            continue

        # No cambiar la base de datos main de Enzonic
        if re.match(r"^(CREATE\s+DATABASE|USE)\b", sentencia, re.I):
            continue

        if re.search(r"\bLOCK\s+TABLES\b", sentencia, re.I):
            continue

        if re.search(r"\bUNLOCK\s+TABLES\b", sentencia, re.I):
            continue

        cursor.execute(sentencia)
        total += 1

        print(f"Sentencia {total} ejecutada correctamente.")

    print("\n¡Importación finalizada!")

    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()

    print("\nTablas encontradas en Enzonic:")

    for tabla in tablas:
        nombre = tabla[0]
        cursor.execute(f"SELECT COUNT(*) FROM `{nombre}`")
        cantidad = cursor.fetchone()[0]
        print(f"- {nombre}: {cantidad} registros")

    cursor.close()

except (pymysql.MySQLError, OSError, UnicodeError, EOFError) as error:
    print("\nERROR DURANTE LA IMPORTACIÓN:")
    print(error)

finally:
    if conexion:
        conexion.close()
        print("\nConexión cerrada.")
