document.addEventListener("DOMContentLoaded", async function () {
    try {
        // 1) Obtener el usuario logueado desde localStorage
        const loggedUserString = localStorage.getItem("loggedUser");
        let loggedUser;
        if (!loggedUserString) {
            console.warn("No hay usuario logueado en localStorage, se tratará como visitante.");
            // Si no hay usuario, se asigna un rol "Visitante"
            loggedUser = { role: "visitante" };
        } else {
            loggedUser = JSON.parse(loggedUserString);
        }
        
        const welcomeMessageElem = document.getElementById("welcomeMessage");

        // 2) Configurar el mensaje de bienvenida según el rol del usuario
        if (loggedUser.role === "administrador") {
            // Para administrador, se muestra el username si existe, de lo contrario 'Administrador'
            welcomeMessageElem.textContent = `Bienvenido, ${loggedUser.username || 'Administrador'}`;
        } else if (loggedUser.role === "visitante") {
            // Si es visitante (no hay sesión iniciada)
            welcomeMessageElem.textContent = "Bienvenido, Visitante";
        } else {
            // Para empleados, inicialmente se muestra un mensaje por defecto; luego se actualiza
            welcomeMessageElem.textContent = "Bienvenido, Usuario";
        }

        // 3) Hacemos fetch a empleados.json para obtener la información de los empleados
        const response = await fetch("/empleados.json");
        if (!response.ok) throw new Error("Error al obtener empleados.json");
        const empleados = await response.json();

        // 4) Actualizar el mensaje de bienvenida para empleados autenticados
        if (loggedUser.role !== "administrador" && loggedUser.role !== "visitante") {
            const empleadoId = parseInt(loggedUser.empleado_id);
            const empleadoRecord = empleados.find(e => e.id === empleadoId);
            if (empleadoRecord) {
                welcomeMessageElem.textContent = `Bienvenido, ${empleadoRecord.nombre || empleadoRecord.username || 'Usuario'}`;
            }
        } else {
            // Si es administrador o visitante, se mantiene el mensaje asignado anteriormente
            if (loggedUser.role === "administrador") {
                welcomeMessageElem.textContent = `Bienvenido, ${loggedUser.username || 'Administrador'}`;
            } else {
                welcomeMessageElem.textContent = "Bienvenido, Visitante";
            }
        }

        // 5) Determinar qué empleados se incluyen en la gráfica:
        // - Si el usuario es administrador o visitante, se muestran todos los empleados.
        // - Si el usuario es empleado, se filtra solo el suyo.
        let empleadosParaLaGrafica = empleados;
        if (loggedUser.role !== "administrador" && loggedUser.role !== "visitante") {
            const empleadoId = parseInt(loggedUser.empleado_id);
            empleadosParaLaGrafica = empleados.filter(e => e.id === empleadoId);
        }
        
        // 6) Obtener el día actual en español para filtrar las tareas
        const diasSemana = ["domingo", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado"];
        const hoy = diasSemana[new Date().getDay()];

        // Variables para contabilizar tareas
        let totalTareas = 0;
        let completadas = 0;
        let pendientes = 0;
        let sinIniciar = 0;
        let extras = 0;

        // 7) Recorrer las tareas asignadas para el día actual de cada empleado seleccionado
        empleadosParaLaGrafica.forEach(empleado => {
            if (empleado.tareas_asignadas && empleado.tareas_asignadas[hoy]) {
                const tareasHoy = empleado.tareas_asignadas[hoy];
                tareasHoy.forEach(tarea => {
                    totalTareas++;
                    // Se asume: 
                    //   estatus 0 => Tarea completada
                    //   estatus 1 => Tarea en progreso (pendiente)
                    //   estatus 2 => Tarea sin iniciar
                    //   estatus 3 => Tarea extra
                    switch (tarea.estatus) {
                        case 0:
                            completadas++;
                            break;
                        case 1:
                            pendientes++;
                            break;
                        case 2:
                            sinIniciar++;
                            break;
                        case 3:
                            extras++;
                            break;
                        default:
                            console.warn(`Estatus desconocido (${tarea.estatus}) en la tarea:`, tarea);
                    }
                });
            }
        });

        // 8) Calcular los porcentajes para cada categoría
        const porcentajeCompletadas = totalTareas > 0 ? (completadas / totalTareas) * 100 : 0;
        const porcentajePendientes = totalTareas > 0 ? (pendientes / totalTareas) * 100 : 0;
        const porcentajeSinIniciar = totalTareas > 0 ? (sinIniciar / totalTareas) * 100 : 0;
        const porcentajeExtras = totalTareas > 0 ? (extras / totalTareas) * 100 : 0;

        // 9) Configuración para la animación del gráfico (basado en el perímetro del círculo)
        // En este ejemplo, todos usan el mismo radio, por lo que el perímetro es de 314.
        const totalCircumference = 314;
        const completedOffset = totalCircumference - (porcentajeCompletadas / 100) * totalCircumference;
        const pendingOffset = totalCircumference - (porcentajePendientes / 100) * totalCircumference;
        const notStartedOffset = totalCircumference - (porcentajeSinIniciar / 100) * totalCircumference;
        const extrasOffset = totalCircumference - (porcentajeExtras / 100) * totalCircumference;

        // Función para animar la transición de valores numéricos
        function animateValue(element, start, end, duration) {
            let startTime = null;
            function step(timestamp) {
                if (!startTime) startTime = timestamp;
                let progress = Math.min((timestamp - startTime) / duration, 1);
                let value = Math.floor(progress * (end - start) + start);
                element.textContent = `${value}%`;
                if (progress < 1) {
                    requestAnimationFrame(step);
                }
            }
            requestAnimationFrame(step);
        }

        // 10) Animar el porcentaje en el centro de la gráfica
        const textElement = document.querySelector(".chart-text span");
        setTimeout(() => animateValue(textElement, 0, porcentajeCompletadas, 1500), 1200);

        // Función auxiliar para manejar cada círculo:
        function handleCircle(selector, count, offsetValue) {
            const circle = document.querySelector(selector);
            if (circle) {
                if (count === 0) {
                    // Remover el círculo del DOM si no hay tareas de ese estatus
                    circle.parentNode.removeChild(circle);
                } else {
                    // Aplicar la animación
                    circle.style.strokeDashoffset = offsetValue;
                }
            }
        }

        // 11) Aplicar la animación a los círculos de progreso con validación
        setTimeout(() => {
            handleCircle(".progress-ring__circle.completed", completadas, completedOffset);
            handleCircle(".progress-ring__circle.pending", pendientes, pendingOffset);
            handleCircle(".progress-ring__circle.not-started", sinIniciar, notStartedOffset);
            handleCircle(".progress-ring__circle.extras", extras, extrasOffset);
        }, 1300);

        // 12) Animación en cascada para mostrar elementos de la página
        function showElement(selector, delay) {
            setTimeout(() => {
                document.querySelector(selector).classList.add("show");
            }, delay);
        }
        showElement("h1", 300);
        showElement(".chart-wrapper", 900);
        showElement(".guia", 1500);

    } catch (error) {
        console.error("Error cargando datos de empleados:", error);
    }
});
