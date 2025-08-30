document.addEventListener("DOMContentLoaded", async function () {
    try {
        // 1) Obtener usuario logueado
        const loggedUserString = localStorage.getItem("loggedUser");
        let loggedUser;
        if (!loggedUserString) {
            console.warn("No hay usuario logueado, será visitante.");
            loggedUser = { role: "visitante" };
        } else {
            loggedUser = JSON.parse(loggedUserString);
        }

        const welcomeMessageElem = document.getElementById("welcomeMessage");

        // 2) Mensaje de bienvenida
        if (loggedUser.role === "admin") {
            welcomeMessageElem.textContent = `Bienvenido, ${loggedUser.username || 'admin'}`;
        } else if (loggedUser.role === "visitante") {
            welcomeMessageElem.textContent = "Bienvenido, Visitante";
        } else {
            welcomeMessageElem.textContent = "Bienvenido, Usuario";
        }

        // 3) Obtener empleados.json
        const response = await fetch("/empleados.json");
        if (!response.ok) throw new Error("Error al obtener empleados.json");
        const empleados = await response.json();

        // 4) Determinar empleados a incluir
        let empleadosParaLaGrafica = empleados;
        if (loggedUser.role !== "admin" && loggedUser.role !== "visitante") {
            const empleadoId = parseInt(loggedUser.empleado_id);
            empleadosParaLaGrafica = empleados.filter(e => e.id === empleadoId);
            const empleadoRecord = empleados.find(e => e.id === empleadoId);
            if (empleadoRecord) {
                welcomeMessageElem.textContent = `Bienvenido, ${empleadoRecord.nombre}`;
            }
        }

        // 5) Días de la semana (en minúsculas, sin tildes)
        const diasSemana = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"];

        // Variables para acumular tareas semanales
        let totalTareas = 0;
        let completadas = 0;
        let pendientes = 0;
        let sinIniciar = 0;
        let extras = 0;

        // 6) Recorrer empleados y tareas de toda la semana
        empleadosParaLaGrafica.forEach(empleado => {
            diasSemana.forEach(dia => {
                if (empleado.tareas_asignadas && empleado.tareas_asignadas[dia]) {
                    empleado.tareas_asignadas[dia].forEach(tarea => {
                        totalTareas++;
                        switch (tarea.estatus) {
                            case 0: // completada
                                completadas++;
                                break;
                            case 1: // en progreso
                                pendientes++;
                                break;
                            case 2: // sin iniciar
                                sinIniciar++;
                                break;
                            case 3: // extra
                            case 4: // extra (desde backend)
                                extras++;
                                break;
                            default:
                                console.warn("Estatus desconocido:", tarea);
                        }
                    });
                }
            });
        });

        // 7) Calcular porcentajes
        const porcentajeCompletadas = totalTareas > 0 ? (completadas / totalTareas) * 100 : 0;
        const porcentajePendientes = totalTareas > 0 ? (pendientes / totalTareas) * 100 : 0;
        const porcentajeSinIniciar = totalTareas > 0 ? (sinIniciar / totalTareas) * 100 : 0;
        const porcentajeExtras = totalTareas > 0 ? (extras / totalTareas) * 100 : 0;

        // 8) Configuración de los círculos
        const totalCircumference = 314;
        const completedOffset = totalCircumference - (porcentajeCompletadas / 100) * totalCircumference;
        const pendingOffset = totalCircumference - (porcentajePendientes / 100) * totalCircumference;
        const notStartedOffset = totalCircumference - (porcentajeSinIniciar / 100) * totalCircumference;
        const extrasOffset = totalCircumference - (porcentajeExtras / 100) * totalCircumference;

        // 9) Texto central → completadas / total
        const textElement = document.querySelector(".chart-text span");
        textElement.textContent = `${completadas}/${totalTareas}`;

        // 10) Aplicar animaciones a los círculos
        function handleCircle(selector, count, offsetValue) {
            const circle = document.querySelector(selector);
            if (circle) {
                if (count === 0) {
                    circle.parentNode.removeChild(circle);
                } else {
                    circle.style.strokeDashoffset = offsetValue;
                }
            }
        }

        setTimeout(() => {
            handleCircle(".progress-ring__circle.completed", completadas, completedOffset);
            handleCircle(".progress-ring__circle.pending", pendientes, pendingOffset);
            handleCircle(".progress-ring__circle.not-started", sinIniciar, notStartedOffset);
            handleCircle(".progress-ring__circle.extras", extras, extrasOffset);
        }, 1000);

        // 11) Animaciones en cascada
        function showElement(selector, delay) {
            setTimeout(() => {
                const elem = document.querySelector(selector);
                if (elem) elem.classList.add("show");
            }, delay);
        }
        showElement("h1", 300);
        showElement(".chart-wrapper", 900);
        showElement(".guia", 1500);

    } catch (error) {
        console.error("Error cargando datos de empleados:", error);
    }
});
