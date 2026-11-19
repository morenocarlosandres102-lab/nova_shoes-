
import pymysql
from getpass import getpass

print("Probando conexión oficial de Enzonic...")

try:
    conn = pymysql.connect(
        host="nova-shoes-db-m33w3x.db.enzonic.com",
        port=3306,
        user="u_f8fenlfjgf",
        password=getpass("Contraseña de Enzonic: "),
        database="main",
        ssl={"ssl": {}},
        connect_timeout=20
    )

    with conn.cursor() as cur:
        cur.execute("SELECT NOW()")
        print("CONEXIÓN EXITOSA:", cur.fetchone())

    conn.close()

except Exception as error:
    print("ERROR:", type(error).__name__)
    print(error)
