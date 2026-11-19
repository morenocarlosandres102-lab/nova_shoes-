from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from decimal import Decimal
from functools import wraps
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("Falta configurar SECRET_KEY en el archivo .env")

# Configuración de imágenes
app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "static", "img"
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

EXTENSIONES_IMAGEN = {"png", "jpg", "jpeg", "webp", "gif"}

# Seguridad de las sesiones
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("COOKIE_SECURE", "False").lower() == "true"
)


# ==========================================
# CONEXIÓN CON MYSQL
# ==========================================

def conectar_db():
    """Establece y devuelve una conexión con la base de datos MySQL."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "0811"),
        database=os.environ.get("DB_NAME", "nova_shoes"),
        port=int(os.environ.get("DB_PORT", "3306")),
        connection_timeout=10
    )

# ==========================================
# CONSULTAR PRODUCTOS
# ==========================================

def obtener_productos():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.id_producto,
            p.nombre,
            p.descripcion,
            p.precio,
            p.stock,
            p.imagen,
            c.nombre AS categoria,
            m.nombre AS marca
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        JOIN marcas m ON p.id_marca = m.id_marca
        ORDER BY p.id_producto DESC
    """)

    productos = cursor.fetchall()
    cursor.close()
    conexion.close()

    return productos


def obtener_productos_por_categoria(categoria):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.id_producto,
            p.nombre,
            p.descripcion,
            p.precio,
            p.stock,
            p.imagen,
            c.nombre AS categoria,
            m.nombre AS marca
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        JOIN marcas m ON p.id_marca = m.id_marca
        WHERE LOWER(TRIM(c.nombre)) = LOWER(TRIM(%s))
        ORDER BY p.id_producto DESC
    """, (categoria,))

    productos = cursor.fetchall()
    cursor.close()
    conexion.close()

    return productos


def obtener_producto(id_producto):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.id_producto,
            p.nombre,
            p.descripcion,
            p.precio,
            p.stock,
            p.imagen,
            c.nombre AS categoria,
            m.nombre AS marca
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        JOIN marcas m ON p.id_marca = m.id_marca
        WHERE p.id_producto = %s
    """, (id_producto,))

    producto = cursor.fetchone()
    cursor.close()
    conexion.close()

    return producto


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@app.route("/")
def inicio():
    productos = obtener_productos()

    return render_template(
        "index.html",
        productos=productos
    )


# ==========================================
# CATEGORÍAS DE LA TIENDA
# ==========================================

@app.route("/hombre")
def hombre():
    productos = obtener_productos_por_categoria("Hombre")
    return render_template("hombre.html", productos=productos)


@app.route("/mujer")
def mujer():
    productos = obtener_productos_por_categoria("Mujer")
    return render_template("mujer.html", productos=productos)


@app.route("/nino")
def nino():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.id_producto,
            p.nombre,
            p.descripcion,
            p.precio,
            p.stock,
            p.imagen,
            c.nombre AS categoria,
            m.nombre AS marca
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        JOIN marcas m ON p.id_marca = m.id_marca
        WHERE LOWER(TRIM(c.nombre)) IN
        ('niño', 'nino', 'niños', 'ninos')
        ORDER BY p.id_producto DESC
    """)

    productos = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template("niño.html", productos=productos)


# ==========================================
# MARCAS
# ==========================================

@app.route("/marcas")
def marcas():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_marca, nombre
        FROM marcas
        ORDER BY nombre
    """)

    marcas_disponibles = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template(
        "marcas.html",
        marcas=marcas_disponibles
    )


# ==========================================
# DETALLE DEL PRODUCTO
# ==========================================

@app.route("/producto/<int:id_producto>")
def producto(id_producto):
    producto_encontrado = obtener_producto(id_producto)

    if producto_encontrado is None:
        return "Producto no encontrado", 404

    return render_template(
        "producto.html",
        producto=producto_encontrado
    )


# ==========================================
# CARRITO DE COMPRAS
# ==========================================

@app.route("/carrito")
def carrito():
    carrito_sesion = session.get("carrito", {})
    productos_carrito = []
    total = Decimal("0.00")

    for id_producto, cantidad in carrito_sesion.items():
        producto = obtener_producto(int(id_producto))

        if producto:
            producto["cantidad"] = cantidad
            producto["subtotal"] = (
                Decimal(str(producto["precio"])) * cantidad
            )

            productos_carrito.append(producto)
            total += producto["subtotal"]

    return render_template(
        "carrito.html",
        carrito=productos_carrito,
        total=total
    )


# ==========================================
# AGREGAR PRODUCTO AL CARRITO
# ==========================================

@app.route("/agregar-carrito/<int:id_producto>", methods=["POST"])
def agregar_carrito(id_producto):
    producto = obtener_producto(id_producto)

    if producto is None:
        flash("El producto no existe.")
        return redirect(url_for("inicio"))

    try:
        cantidad = int(request.form.get("cantidad", 1))
    except (ValueError, TypeError):
        cantidad = 1

    if cantidad < 1:
        flash("La cantidad no es válida.")
        return redirect(url_for("producto", id_producto=id_producto))

    carrito_sesion = session.get("carrito", {})
    cantidad_actual = carrito_sesion.get(str(id_producto), 0)

    if cantidad_actual + cantidad > producto["stock"]:
        flash("No hay suficientes unidades disponibles.")
        return redirect(url_for("producto", id_producto=id_producto))

    carrito_sesion[str(id_producto)] = cantidad_actual + cantidad
    session["carrito"] = carrito_sesion

    flash("Producto agregado al carrito.")
    return redirect(url_for("carrito"))


# ==========================================
# ELIMINAR PRODUCTO DEL CARRITO
# ==========================================

@app.route("/eliminar-carrito/<int:id_producto>", methods=["POST"])
def eliminar_carrito(id_producto):
    carrito_sesion = session.get("carrito", {})
    carrito_sesion.pop(str(id_producto), None)
    session["carrito"] = carrito_sesion

    flash("Producto eliminado del carrito.")
    return redirect(url_for("carrito"))


# ==========================================
# REGISTRO DE USUARIOS
# ==========================================

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar_password", "")

        if not nombre or not correo or not password:
            return render_template(
                "registro.html",
                error="Todos los campos son obligatorios."
            )

        if password != confirmar:
            return render_template(
                "registro.html",
                error="Las contraseñas no coinciden."
            )

        if len(password) < 8:
            return render_template(
                "registro.html",
                error="La contraseña debe tener al menos 8 caracteres."
            )

        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id_usuario FROM usuarios WHERE correo = %s",
                (correo,)
            )

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                return render_template(
                    "registro.html",
                    error="Este correo ya está registrado."
                )

            password_hash = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO usuarios
                (nombre, correo, `contraseña`, rol)
                VALUES (%s, %s, %s, 'cliente')
            """, (nombre, correo, password_hash))

            conexion.commit()

            flash("Cuenta creada correctamente. Ahora puedes iniciar sesión.")
            return redirect(url_for("login"))

        except mysql.connector.Error:
            conexion.rollback()
            flash("No fue posible crear la cuenta.")
            return redirect(url_for("registro"))

        finally:
            cursor.close()
            conexion.close()

    return render_template("registro.html")


# ==========================================
# INICIO DE SESIÓN DE CLIENTES
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT id_usuario, nombre, correo, `contraseña`, rol
                FROM usuarios
                WHERE correo = %s
            """, (correo,))

            usuario = cursor.fetchone()

            if usuario and check_password_hash(
                usuario["contraseña"], password
            ):
                session.clear()
                session["id_usuario"] = usuario["id_usuario"]
                session["nombre"] = usuario["nombre"]
                session["correo"] = usuario["correo"]
                session["rol"] = usuario["rol"]

                flash("Bienvenido a Nova Shoes.")
                return redirect(url_for("inicio"))

            return render_template(
                "login.html",
                error="Correo o contraseña incorrectos."
            )

        finally:
            cursor.close()
            conexion.close()

    return render_template("login.html")


# ==========================================
# CERRAR SESIÓN DE CLIENTES
# ==========================================

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.")
    return redirect(url_for("inicio"))


# ==========================================
# MI CUENTA
# ==========================================

@app.route("/mi-cuenta")
def mi_cuenta():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id_usuario, nombre, correo, rol
            FROM usuarios
            WHERE id_usuario = %s
        """, (session["id_usuario"],))

        usuario = cursor.fetchone()

        cursor.execute("""
            SELECT id_pedido, fecha, total, estado
            FROM pedidos
            WHERE id_usuario = %s
            ORDER BY fecha DESC
        """, (session["id_usuario"],))

        pedidos = cursor.fetchall()

        return render_template(
            "mi_cuenta.html",
            usuario=usuario,
            pedidos=pedidos
        )

    finally:
        cursor.close()
        conexion.close()

        # ==========================================
# CHECKOUT Y REGISTRO DE PEDIDOS
# ==========================================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "id_usuario" not in session:
        flash("Debes iniciar sesión para comprar.")
        return redirect(url_for("login"))

    carrito_sesion = session.get("carrito", {})

    if not carrito_sesion:
        flash("Tu carrito está vacío.")
        return redirect(url_for("carrito"))

    productos_carrito = []
    total = Decimal("0.00")

    for id_producto, cantidad in carrito_sesion.items():
        producto = obtener_producto(int(id_producto))

        if producto is None:
            flash("Uno de los productos ya no está disponible.")
            return redirect(url_for("carrito"))

        producto["cantidad"] = cantidad
        producto["subtotal"] = (
            Decimal(str(producto["precio"])) * cantidad
        )

        productos_carrito.append(producto)
        total += producto["subtotal"]

    if request.method == "POST":
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        try:
            conexion.start_transaction()

            # Verificar nuevamente el inventario
            for item in productos_carrito:
                cursor.execute("""
                    SELECT stock
                    FROM productos
                    WHERE id_producto = %s
                    FOR UPDATE
                """, (item["id_producto"],))

                inventario = cursor.fetchone()

                if (
                    inventario is None
                    or inventario["stock"] < item["cantidad"]
                ):
                    raise ValueError(
                        f"Stock insuficiente para {item['nombre']}."
                    )

            # Crear el pedido
            cursor.execute("""
                INSERT INTO pedidos (id_usuario, total, estado)
                VALUES (%s, %s, 'pendiente')
            """, (session["id_usuario"], total))

            id_pedido = cursor.lastrowid

            # Registrar los productos comprados
            for item in productos_carrito:
                cursor.execute("""
                    INSERT INTO detalle_pedido
                    (id_pedido, id_producto, cantidad, precio)
                    VALUES (%s, %s, %s, %s)
                """, (
                    id_pedido,
                    item["id_producto"],
                    item["cantidad"],
                    item["precio"]
                ))

                # Descontar existencias
                cursor.execute("""
                    UPDATE productos
                    SET stock = stock - %s
                    WHERE id_producto = %s
                """, (
                    item["cantidad"],
                    item["id_producto"]
                ))

            conexion.commit()
            session.pop("carrito", None)

            flash("¡Tu pedido fue registrado correctamente!")
            return redirect(url_for("mi_cuenta"))

        except ValueError as error:
            conexion.rollback()
            flash(str(error))
            return redirect(url_for("carrito"))

        except Exception:
            conexion.rollback()
            app.logger.exception("Error al registrar el pedido")
            flash("No fue posible registrar el pedido.")
            return redirect(url_for("checkout"))

        finally:
            cursor.close()
            conexion.close()

    return render_template(
        "checkout.html",
        carrito=productos_carrito,
        total=total
    )


# ==========================================
# NOSOTROS
# ==========================================

@app.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")


# ==========================================
# CONTACTO
# ==========================================

@app.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        asunto = request.form.get("asunto", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        if not all([nombre, correo, asunto, mensaje]):
            flash("Completa todos los campos.")
            return redirect(url_for("contacto"))

        flash("Mensaje recibido. Gracias por comunicarte con nosotros.")
        return redirect(url_for("contacto"))

    return render_template("contacto.html")


# ==========================================
# ERROR 404
# ==========================================

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return """
    <h1>Página no encontrada</h1>
    <p>Verifica la dirección que estás utilizando.</p>
    <a href="/">Volver al inicio</a>
    """, 404


# ==========================================
# SEGURIDAD DEL ADMINISTRADOR
# ==========================================

def administrador_requerido(funcion):
    @wraps(funcion)
    def decorada(*args, **kwargs):
        if (
            not session.get("id_usuario")
            or session.get("rol") != "admin"
        ):
            flash("Debes iniciar sesión como administrador.", "warning")
            return redirect(url_for("login_admin"))

        return funcion(*args, **kwargs)

    return decorada


# ==========================================
# GUARDAR IMÁGENES
# ==========================================

def guardar_imagen(archivo):
    if not archivo or not archivo.filename:
        return None

    nombre_seguro = secure_filename(archivo.filename)

    if "." not in nombre_seguro:
        raise ValueError("El archivo no tiene una extensión válida.")

    extension = nombre_seguro.rsplit(".", 1)[1].lower()

    if extension not in EXTENSIONES_IMAGEN:
        raise ValueError(
            "Formato no permitido. Usa PNG, JPG, JPEG, WEBP o GIF."
        )

    import uuid

    nombre_final = f"{uuid.uuid4().hex}.{extension}"

    ruta = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nombre_final
    )

    archivo.save(ruta)

    return nombre_final


# ==========================================
# CONSULTAR CATEGORÍAS Y MARCAS
# ==========================================

def obtener_categorias_marcas(cursor):
    cursor.execute("""
        SELECT id_categoria, nombre
        FROM categorias
        ORDER BY nombre
    """)
    categorias = cursor.fetchall()

    cursor.execute("""
        SELECT id_marca, nombre
        FROM marcas
        ORDER BY nombre
    """)
    marcas = cursor.fetchall()

    return categorias, marcas


# ==========================================
# LOGIN DEL ADMINISTRADOR
# ==========================================

@app.route("/admin/login", methods=["GET", "POST"])
def login_admin():
    if session.get("rol") == "admin":
        return redirect(url_for("dashboard_admin"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        conexion = None
        cursor = None

        try:
            conexion = conectar_db()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    id_usuario,
                    nombre,
                    correo,
                    `contraseña`,
                    rol
                FROM usuarios
                WHERE correo = %s
                AND rol = 'admin'
                LIMIT 1
            """, (correo,))

            administrador = cursor.fetchone()

            if administrador and check_password_hash(
                administrador["contraseña"],
                password
            ):
                session.clear()

                session["id_usuario"] = administrador["id_usuario"]
                session["nombre"] = administrador["nombre"]
                session["correo"] = administrador["correo"]
                session["rol"] = administrador["rol"]

                flash(
                    "Bienvenido al panel administrativo.",
                    "success"
                )

                return redirect(url_for("dashboard_admin"))

            return render_template(
                "admin/login_admin.html",
                error="Correo o contraseña incorrectos."
            )

        except mysql.connector.Error:
            app.logger.exception("Error al iniciar sesión de administrador")

            return render_template(
                "admin/login_admin.html",
                error="No fue posible iniciar sesión. Verifica la conexión."
            )

        finally:
            if cursor:
                cursor.close()

            if conexion and conexion.is_connected():
                conexion.close()

    return render_template("admin/login_admin.html")

# ==========================================
# DASHBOARD DEL ADMINISTRADOR
# ==========================================

@app.route("/admin/dashboard")
@administrador_requerido
def dashboard_admin():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM productos
        """)
        total_productos = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM usuarios
            WHERE rol = 'cliente' OR rol IS NULL
        """)
        total_clientes = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
        """)
        total_pedidos = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) AS total
            FROM pedidos
        """)
        total_registrado = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT
                p.id_pedido,
                u.nombre,
                p.fecha,
                p.total,
                p.estado
            FROM pedidos p
            INNER JOIN usuarios u
                ON p.id_usuario = u.id_usuario
            ORDER BY p.fecha DESC, p.id_pedido DESC
            LIMIT 8
        """)
        pedidos_recientes = cursor.fetchall()

        cursor.execute("""
            SELECT nombre, precio, stock
            FROM productos
            WHERE stock <= 5
            ORDER BY stock ASC, nombre ASC
            LIMIT 10
        """)
        productos_bajo_stock = cursor.fetchall()

        return render_template(
            "admin/dashboard.html",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_pedidos=total_pedidos,
            total_registrado=total_registrado,
            pedidos_recientes=pedidos_recientes,
            productos_bajo_stock=productos_bajo_stock
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# LISTAR PRODUCTOS
# ==========================================

@app.route("/admin/productos")
@administrador_requerido
def admin_productos():
    buscar = request.args.get("buscar", "").strip()

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        consulta = """
            SELECT
                p.id_producto,
                p.nombre,
                p.descripcion,
                p.precio,
                p.stock,
                p.imagen,
                p.id_categoria,
                p.id_marca,
                c.nombre AS categoria,
                m.nombre AS marca
            FROM productos p
            INNER JOIN categorias c
                ON p.id_categoria = c.id_categoria
            INNER JOIN marcas m
                ON p.id_marca = m.id_marca
        """

        if buscar:
            cursor.execute(
                consulta + """
                    WHERE p.nombre LIKE %s
                    OR c.nombre LIKE %s
                    OR m.nombre LIKE %s
                    ORDER BY p.id_producto DESC
                """,
                (
                    f"%{buscar}%",
                    f"%{buscar}%",
                    f"%{buscar}%"
                )
            )
        else:
            cursor.execute(
                consulta + " ORDER BY p.id_producto DESC"
            )

        productos = cursor.fetchall()

        return render_template(
            "admin/productos.html",
            productos=productos,
            buscar=buscar
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# AGREGAR PRODUCTO
# ==========================================

@app.route("/admin/productos/agregar", methods=["GET", "POST"])
@administrador_requerido
def admin_agregar_producto():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            imagen_archivo = request.files.get("imagen")

            try:
                precio = Decimal(request.form.get("precio", "0"))
                stock = int(request.form.get("stock", "0"))
                id_categoria = int(
                    request.form.get("id_categoria", "0")
                )
                id_marca = int(
                    request.form.get("id_marca", "0")
                )

                imagen = guardar_imagen(imagen_archivo)

            except (ValueError, TypeError, ArithmeticError) as error:
                flash(str(error), "danger")

                categorias, marcas = obtener_categorias_marcas(cursor)

                return render_template(
                    "admin/agregar_producto.html",
                    categorias=categorias,
                    marcas=marcas
                )

            if (
                not nombre
                or precio <= 0
                or stock < 0
                or not id_categoria
                or not id_marca
            ):
                flash(
                    "Completa los campos correctamente. "
                    "El precio debe ser mayor que cero.",
                    "danger"
                )

            else:
                cursor.execute("""
                    INSERT INTO productos (
                        nombre,
                        descripcion,
                        precio,
                        stock,
                        imagen,
                        id_categoria,
                        id_marca
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    nombre,
                    descripcion,
                    precio,
                    stock,
                    imagen,
                    id_categoria,
                    id_marca
                ))

                conexion.commit()

                flash(
                    "Producto agregado correctamente.",
                    "success"
                )

                return redirect(url_for("admin_productos"))

        categorias, marcas = obtener_categorias_marcas(cursor)

        return render_template(
            "admin/agregar_producto.html",
            categorias=categorias,
            marcas=marcas
        )

    except Exception:
        conexion.rollback()
        app.logger.exception("Error al agregar producto")

        flash(
            "No fue posible guardar el producto. "
            "Revisa los datos y las relaciones.",
            "danger"
        )

        categorias, marcas = obtener_categorias_marcas(cursor)

        return render_template(
            "admin/agregar_producto.html",
            categorias=categorias,
            marcas=marcas
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# EDITAR PRODUCTO
# ==========================================

@app.route(
    "/admin/productos/editar/<int:id_producto>",
    methods=["GET", "POST"]
)
@administrador_requerido
def admin_editar_producto(id_producto):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM productos
            WHERE id_producto = %s
        """, (id_producto,))

        producto = cursor.fetchone()

        if not producto:
            flash("El producto no existe.", "warning")
            return redirect(url_for("admin_productos"))

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            archivo = request.files.get("imagen")

            try:
                precio = Decimal(request.form.get("precio", "0"))
                stock = int(request.form.get("stock", "0"))
                id_categoria = int(
                    request.form.get("id_categoria", "0")
                )
                id_marca = int(
                    request.form.get("id_marca", "0")
                )

                nueva_imagen = guardar_imagen(archivo)

            except (ValueError, TypeError, ArithmeticError) as error:
                flash(str(error), "danger")

                categorias, marcas = obtener_categorias_marcas(cursor)

                return render_template(
                    "admin/editar_producto.html",
                    producto=producto,
                    categorias=categorias,
                    marcas=marcas
                )

            if (
                not nombre
                or precio <= 0
                or stock < 0
                or not id_categoria
                or not id_marca
            ):
                flash(
                    "Completa los campos correctamente.",
                    "danger"
                )

            else:
                imagen = (
                    nueva_imagen
                    if nueva_imagen
                    else producto["imagen"]
                )

                cursor.execute("""
                    UPDATE productos
                    SET
                        nombre = %s,
                        descripcion = %s,
                        precio = %s,
                        stock = %s,
                        imagen = %s,
                        id_categoria = %s,
                        id_marca = %s
                    WHERE id_producto = %s
                """, (
                    nombre,
                    descripcion,
                    precio,
                    stock,
                    imagen,
                    id_categoria,
                    id_marca,
                    id_producto
                ))

                conexion.commit()

                flash(
                    "Producto actualizado correctamente.",
                    "success"
                )

                return redirect(url_for("admin_productos"))

        categorias, marcas = obtener_categorias_marcas(cursor)

        return render_template(
            "admin/editar_producto.html",
            producto=producto,
            categorias=categorias,
            marcas=marcas
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# ELIMINAR PRODUCTO
# ==========================================

@app.route(
    "/admin/productos/eliminar/<int:id_producto>",
    methods=["POST"]
)
@administrador_requerido
def admin_eliminar_producto(id_producto):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            DELETE FROM productos
            WHERE id_producto = %s
        """, (id_producto,))

        conexion.commit()

        flash(
            "Producto eliminado correctamente.",
            "success"
        )

    except mysql.connector.IntegrityError:
        conexion.rollback()

        flash(
            "No se puede eliminar: el producto está asociado "
            "a uno o más pedidos.",
            "warning"
        )

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("admin_productos"))

# ==========================================
# CATEGORÍAS
# ==========================================

@app.route("/admin/categorias", methods=["GET", "POST"])
@administrador_requerido
def admin_categorias():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()

            if not nombre:
                flash(
                    "Escribe el nombre de la categoría.",
                    "warning"
                )

            else:
                cursor.execute("""
                    INSERT INTO categorias (nombre)
                    VALUES (%s)
                """, (nombre,))

                conexion.commit()

                flash(
                    "Categoría agregada correctamente.",
                    "success"
                )

                return redirect(url_for("admin_categorias"))

        cursor.execute("""
            SELECT id_categoria, nombre
            FROM categorias
            ORDER BY nombre
        """)

        categorias = cursor.fetchall()

        return render_template(
            "admin/categorias.html",
            categorias=categorias
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# ELIMINAR CATEGORÍA
# ==========================================

@app.route(
    "/admin/categorias/eliminar/<int:id_categoria>",
    methods=["POST"]
)
@administrador_requerido
def admin_eliminar_categoria(id_categoria):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            DELETE FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        conexion.commit()

        flash(
            "Categoría eliminada correctamente.",
            "success"
        )

    except mysql.connector.IntegrityError:
        conexion.rollback()

        flash(
            "No se puede eliminar esta categoría "
            "porque tiene productos asociados.",
            "warning"
        )

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("admin_categorias"))


# ==========================================
# MARCAS
# ==========================================

@app.route("/admin/marcas", methods=["GET", "POST"])
@administrador_requerido
def admin_marcas():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()

            if not nombre:
                flash(
                    "Escribe el nombre de la marca.",
                    "warning"
                )

            else:
                cursor.execute("""
                    INSERT INTO marcas (nombre)
                    VALUES (%s)
                """, (nombre,))

                conexion.commit()

                flash(
                    "Marca agregada correctamente.",
                    "success"
                )

                return redirect(url_for("admin_marcas"))

        cursor.execute("""
            SELECT id_marca, nombre
            FROM marcas
            ORDER BY nombre
        """)

        marcas = cursor.fetchall()

        return render_template(
            "admin/marcas.html",
            marcas=marcas
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# ELIMINAR MARCA
# ==========================================

@app.route(
    "/admin/marcas/eliminar/<int:id_marca>",
    methods=["POST"]
)
@administrador_requerido
def admin_eliminar_marca(id_marca):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            DELETE FROM marcas
            WHERE id_marca = %s
        """, (id_marca,))

        conexion.commit()

        flash(
            "Marca eliminada correctamente.",
            "success"
        )

    except mysql.connector.IntegrityError:
        conexion.rollback()

        flash(
            "No se puede eliminar esta marca "
            "porque tiene productos asociados.",
            "warning"
        )

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("admin_marcas"))


# ==========================================
# INVENTARIO
# ==========================================

@app.route("/admin/inventario")
@administrador_requerido
def admin_inventario():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id_producto,
                nombre,
                precio,
                stock
            FROM productos
            ORDER BY stock ASC, nombre ASC
        """)

        productos = cursor.fetchall()

        return render_template(
            "admin/inventario.html",
            productos=productos
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# LISTAR PEDIDOS
# ==========================================

@app.route("/admin/pedidos")
@administrador_requerido
def admin_pedidos():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.id_pedido,
                u.nombre,
                p.fecha,
                p.total,
                p.estado
            FROM pedidos p
            INNER JOIN usuarios u
                ON p.id_usuario = u.id_usuario
            ORDER BY p.fecha DESC, p.id_pedido DESC
        """)

        pedidos = cursor.fetchall()

        return render_template(
            "admin/pedidos.html",
            pedidos=pedidos
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# DETALLE Y ACTUALIZACIÓN DEL PEDIDO
# ==========================================

@app.route(
    "/admin/pedidos/<int:id_pedido>",
    methods=["GET", "POST"]
)
@administrador_requerido
def admin_detalle_pedido(id_pedido):
    estados_permitidos = {
        "pendiente",
        "procesando",
        "enviado",
        "completado",
        "cancelado"
    }

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        if request.method == "POST":
            nuevo_estado = request.form.get(
                "estado", ""
            ).strip().lower()

            if nuevo_estado not in estados_permitidos:
                flash(
                    "El estado seleccionado no es válido.",
                    "danger"
                )

            else:
                cursor.execute("""
                    UPDATE pedidos
                    SET estado = %s
                    WHERE id_pedido = %s
                """, (nuevo_estado, id_pedido))

                conexion.commit()

                flash(
                    "Estado del pedido actualizado.",
                    "success"
                )

                return redirect(
                    url_for(
                        "admin_detalle_pedido",
                        id_pedido=id_pedido
                    )
                )

        cursor.execute("""
            SELECT
                p.id_pedido,
                u.nombre,
                u.correo,
                p.fecha,
                p.total,
                p.estado
            FROM pedidos p
            INNER JOIN usuarios u
                ON p.id_usuario = u.id_usuario
            WHERE p.id_pedido = %s
        """, (id_pedido,))

        pedido = cursor.fetchone()

        if not pedido:
            flash("El pedido no existe.", "warning")
            return redirect(url_for("admin_pedidos"))

        cursor.execute("""
            SELECT
                pr.nombre,
                dp.cantidad,
                dp.precio
            FROM detalle_pedido dp
            INNER JOIN productos pr
                ON dp.id_producto = pr.id_producto
            WHERE dp.id_pedido = %s
        """, (id_pedido,))

        detalles = cursor.fetchall()

        return render_template(
            "admin/detalle_pedido.html",
            pedido=pedido,
            detalles=detalles
        )

    finally:
        cursor.close()
        conexion.close()

        # ==========================================
# CLIENTES
# ==========================================

@app.route("/admin/clientes")
@administrador_requerido
def admin_clientes():
    buscar = request.args.get("buscar", "").strip()

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        consulta = """
            SELECT
                id_usuario,
                nombre,
                correo,
                rol
            FROM usuarios
            WHERE rol = 'cliente' OR rol IS NULL
        """

        if buscar:
            consulta += """
                AND (
                    nombre LIKE %s
                    OR correo LIKE %s
                )
            """

            cursor.execute(
                consulta + " ORDER BY id_usuario DESC",
                (
                    f"%{buscar}%",
                    f"%{buscar}%"
                )
            )

        else:
            cursor.execute(
                consulta + " ORDER BY id_usuario DESC"
            )

        clientes = cursor.fetchall()

        return render_template(
            "admin/clientes.html",
            clientes=clientes,
            buscar=buscar
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# REPORTES
# ==========================================

@app.route("/admin/reportes")
@administrador_requerido
def admin_reportes():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM productos
        """)
        total_productos = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM usuarios
            WHERE rol = 'cliente' OR rol IS NULL
        """)
        total_clientes = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
        """)
        total_pedidos = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) AS total
            FROM pedidos
        """)
        total_registrado = cursor.fetchone()["total"]

        return render_template(
            "admin/reportes.html",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_pedidos=total_pedidos,
            total_registrado=total_registrado
        )

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# CERRAR SESIÓN DEL ADMINISTRADOR
# ==========================================

@app.route("/admin/logout")
def logout_admin():
    if session.get("rol") == "admin":
        session.clear()

    flash(
        "Has cerrado sesión correctamente.",
        "success"
    )

    return redirect(url_for("login_admin"))


# ==========================================
# INICIAR SERVIDOR
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)