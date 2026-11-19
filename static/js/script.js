
document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // CARRITO
    // =========================

    let carrito = JSON.parse(localStorage.getItem("carritoNova")) || [];

    const botonesCarrito = document.querySelectorAll(".boton-carrito-producto");
    const contadorCarrito = document.querySelector(".contador-carrito");
    const botonCarrito = document.querySelector(".boton-carrito");

    function guardarCarrito() {
        localStorage.setItem("carritoNova", JSON.stringify(carrito));
    }

    function actualizarContador() {
        if (contadorCarrito) {
            contadorCarrito.textContent = carrito.reduce(
                (total, producto) => total + producto.cantidad, 0
            );
        }
    }

    botonesCarrito.forEach((boton) => {

        boton.addEventListener("click", () => {

            const tarjeta = boton.closest(".producto-card");

            const nombre = tarjeta.querySelector("h3").textContent.trim();
            const marca = tarjeta.querySelector(".producto-marca").textContent.trim();
            const precio = tarjeta.querySelector(".producto-precio").textContent.trim();
            const id = boton.dataset.id;

            const existente = carrito.find(producto => producto.id == id);

            if (existente) {
                existente.cantidad++;
            } else {
                carrito.push({
                    id: id,
                    nombre: nombre,
                    marca: marca,
                    precio: precio,
                    cantidad: 1
                });
            }

            guardarCarrito();
            actualizarContador();

            boton.textContent = "Agregado ✓";

            setTimeout(() => {
                boton.textContent = "Agregar al carrito";
            }, 1500);

            console.log("Carrito actualizado:", carrito);
        });

    });

    if (botonCarrito) {

        botonCarrito.addEventListener("click", () => {

            if (carrito.length === 0) {
                alert("Tu carrito está vacío");
                return;
            }

            let mensaje = "PRODUCTOS EN TU CARRITO\n\n";

            carrito.forEach((producto) => {
                mensaje += `${producto.nombre}\n`;
                mensaje += `Cantidad: ${producto.cantidad}\n`;
                mensaje += `Precio: ${producto.precio}\n\n`;
            });

            alert(mensaje);
        });

    }

    actualizarContador();


    // =========================
    // BUSQUEDA
    // =========================

    const botonBuscar = document.querySelector(".boton-buscar");

    if (botonBuscar) {

        botonBuscar.addEventListener("click", () => {

            const busqueda = prompt("¿Qué producto estás buscando?");

            if (!busqueda) return;

            const productos = document.querySelectorAll(".producto-card");
            let encontrados = 0;

            productos.forEach((producto) => {

                const texto = producto.textContent.toLowerCase();

                if (texto.includes(busqueda.toLowerCase())) {
                    producto.style.display = "";
                    encontrados++;
                } else {
                    producto.style.display = "none";
                }

            });

            if (encontrados === 0) {
                alert("No encontramos productos con ese nombre.");
            }

            const seccion = document.querySelector("#productos");

            if (seccion) {
                seccion.scrollIntoView({ behavior: "smooth" });
            }

        });

    }


    // =========================
    // USUARIO
    // =========================

    const botonUsuario = document.querySelector(".boton-usuario");

    if (botonUsuario) {

        botonUsuario.addEventListener("click", () => {
            alert("Próximamente podrás iniciar sesión en Nova Shoes.");
        });

    }


    // =========================
    // BOTONES PRINCIPALES
    // =========================

    const botonesComprar = document.querySelectorAll(".boton-principal");

    botonesComprar.forEach((boton) => {

        boton.addEventListener("click", () => {

            const destino = boton.getAttribute("href");

            if (destino && destino.startsWith("#")) {

                const seccion = document.querySelector(destino);

                if (seccion) {
                    seccion.scrollIntoView({ behavior: "smooth" });
                }

            }

        });

    });


    // =========================
    // EFECTOS DE PRODUCTOS
    // =========================

    const productos = document.querySelectorAll(".producto-card");

    productos.forEach((producto) => {

        producto.addEventListener("mouseenter", () => {
            producto.style.transform = "translateY(-5px)";
            producto.style.transition = "transform 0.3s ease";
        });

        producto.addEventListener("mouseleave", () => {
            producto.style.transform = "translateY(0)";
        });

    });


    // =========================
    // LOGO
    // =========================

    const logo = document.querySelector(".logo a");

    if (logo) {

        logo.addEventListener("click", (evento) => {

            evento.preventDefault();

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });

        });

    }

    console.log("JavaScript de Nova Shoes funcionando");

});
