document.addEventListener("DOMContentLoaded", () => {



    let carrito = [];

    const botonesCarrito = document.querySelectorAll(".boton-carrito-producto");
    const contadorCarrito = document.querySelector(".contador-carrito");
    const botonCarrito = document.querySelector(".boton-carrito");

    botonesCarrito.forEach((boton) => {

        boton.addEventListener("click", () => {

            const tarjeta = boton.closest(".producto-card");

            const nombre = tarjeta.querySelector("h3").textContent.trim();
            const marca = tarjeta.querySelector(".producto-marca").textContent.trim();
            const precio = tarjeta.querySelector(".producto-precio").textContent.trim();
            const id = boton.dataset.id;

            const producto = {
                id: id,
                nombre: nombre,
                marca: marca,
                precio: precio
            };

            carrito.push(producto);

            actualizarContador();

            boton.textContent = "Agregado ✓";

            setTimeout(() => {
                boton.textContent = "Agregar al carrito";
            }, 1500);

            console.log("Producto agregado:", producto);
        });

    });


    function actualizarContador() {

        if (contadorCarrito) {
            contadorCarrito.textContent = carrito.length;
        }

    }



    if (botonCarrito) {

        botonCarrito.addEventListener("click", () => {

            if (carrito.length === 0) {

                alert("Tu carrito está vacío");

            } else {

                let mensaje = "Productos en tu carrito:\n\n";

                carrito.forEach((producto, indice) => {

                    mensaje += `${indice + 1}. ${producto.nombre} - ${producto.precio}\n`;

                });

                alert(mensaje);
            }

        });

    }


    // =========================
    // BUSQUEDA
    // =========================

    const botonBuscar = document.querySelector(".boton-buscar");

    if (botonBuscar) {

        botonBuscar.addEventListener("click", () => {

            const busqueda = prompt("¿Qué producto estás buscando?");

            if (!busqueda) {
                return;
            }

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

            document.querySelector("#productos").scrollIntoView({
                behavior: "smooth"
            });

        });

    }


   

    const botonUsuario = document.querySelector(".boton-usuario");

    if (botonUsuario) {

        botonUsuario.addEventListener("click", () => {

            alert("Próximamente podrás iniciar sesión en Nova Shoes.");

        });

    }


    
    const botonesComprar = document.querySelectorAll(".boton-principal");

    botonesComprar.forEach((boton) => {

        boton.addEventListener("click", () => {

            const destino = boton.getAttribute("href");

            if (destino && destino.startsWith("#")) {

                const seccion = document.querySelector(destino);

                if (seccion) {

                    seccion.scrollIntoView({
                        behavior: "smooth"
                    });

                }

            }

        });

    });


    
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