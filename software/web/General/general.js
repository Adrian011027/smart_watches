// Array de días en español (0=domingo,...6=sábado)
const diasSemana = ["domingo", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado"];

// Día que se está mostrando
let currentDayIndex = new Date().getDay();
let trabajadores = [];

// Paginación de empleados
let currentEmpPage = 0;
const pageSize = 5; // 5 columnas fijas en la tabla

document.addEventListener('DOMContentLoaded', async () => {
  // --- 1) Fade-in al título ---
  const titulo = document.querySelector("h2");
  titulo.classList.add("fade-in");
  setTimeout(() => {
    titulo.classList.add("show");
  }, 100);

  // --- 2) Al terminar el título, fade-in al reloj ---
  const clockContainer = document.querySelector(".clock-container");
  setTimeout(() => {
    clockContainer.classList.add("show");
  }, 500); 
  // Esperamos ~1.5s para que el título se muestre completo 
  // antes de iniciar el reloj
  
  // --- 3) Al terminar el reloj, fade-in a la tabla ---
  const tableWrapper = document.getElementById("table-wrapper");
  setTimeout(() => {
    tableWrapper.classList.add("show");
  }, 1000); 
  // Esperamos ~1s totales, de modo que:
  // Título se ve primero, luego el reloj y finalmente la tabla

  // Referencias a botones
  const nextDayBtn = document.getElementById('next-day-btn');
  const todayBtn = document.getElementById('today-btn');
  const prevEmpBtn = document.getElementById('prev-emp-page');
  const nextEmpBtn = document.getElementById('next-emp-page');

  try {
    // Obtener la lista de empleados desde un JSON
    const response = await fetch('/empleados.json');
    if (!response.ok) throw new Error('Error al obtener los empleados');
    trabajadores = await response.json();

    // Cargamos las actividades del día actual
    loadTasksForDay(currentDayIndex);

  } catch (error) {
    console.error("Error al cargar los empleados:", error);
  }

  // Listeners: cambiar de día
  nextDayBtn.addEventListener('click', () => {
    animateDayChange("left", () => {
      currentDayIndex = (currentDayIndex + 1) % 7; // 0..6 cíclico
      loadTasksForDay(currentDayIndex);
    });
  });

  todayBtn.addEventListener('click', () => {
    animateDayChange("right", () => {
      currentDayIndex = new Date().getDay();
      loadTasksForDay(currentDayIndex);
    });
  });

  // Listeners: paginación de empleados
  prevEmpBtn.addEventListener('click', () => {
    if (currentEmpPage > 0) {
      animateEmpPageChange("right", () => {
        currentEmpPage--;
        loadTasksForDay(currentDayIndex);
      });
    }
  });

  nextEmpBtn.addEventListener('click', () => {
    const maxPage = Math.floor((trabajadores.length - 1) / pageSize);
    if (currentEmpPage < maxPage) {
      animateEmpPageChange("left", () => {
        currentEmpPage++;
        loadTasksForDay(currentDayIndex);
      });
    }
  });

  // Inicia la actualización continua del reloj
  requestAnimationFrame(updateTime);
});

/** 
 * Animación para cambiar la página de empleados (flechas der/izq)
 */
function animateEmpPageChange(direction, onComplete) {
  const tableWrapper = document.getElementById("table-wrapper");
  let exitClass, enterClass;

  if (direction === "left") {
    exitClass = "slide-left-exit";
    enterClass = "slide-left-enter";
  } else {
    exitClass = "slide-right-exit";
    enterClass = "slide-right-enter";
  }

  tableWrapper.classList.add(exitClass);

  function handleExitEnd(e) {
    e.target.classList.remove(exitClass);
    tableWrapper.removeEventListener("animationend", handleExitEnd);
    onComplete();
    tableWrapper.classList.add(enterClass);

    function handleEnterEnd(e2) {
      e2.target.classList.remove(enterClass);
      tableWrapper.removeEventListener("animationend", handleEnterEnd);
    }
    tableWrapper.addEventListener("animationend", handleEnterEnd);
  }
  tableWrapper.addEventListener("animationend", handleExitEnd);
}

/**
 * Animación para cambiar de día (flechas en el reloj)
 */
function animateDayChange(direction, onComplete) {
  const tableWrapper = document.getElementById("table-wrapper");
  const tasksDayLabel = document.getElementById("tasks-day");

  let exitClass, enterClass;
  if (direction === "left") {
    exitClass = "slide-left-exit";
    enterClass = "slide-left-enter";
  } else {
    exitClass = "slide-right-exit";
    enterClass = "slide-right-enter";
  }

  tableWrapper.classList.add(exitClass);
  tasksDayLabel.classList.add(exitClass);

  let elementsExited = 0;
  function handleExitEnd(e) {
    e.target.classList.remove(exitClass);
    elementsExited++;
    if (elementsExited === 2) {
      tableWrapper.removeEventListener("animationend", handleExitEnd);
      tasksDayLabel.removeEventListener("animationend", handleExitEnd);
      onComplete();

      tableWrapper.classList.add(enterClass);
      tasksDayLabel.classList.add(enterClass);

      let elementsEntered = 0;
      function handleEnterEnd(e2) {
        e2.target.classList.remove(enterClass);
        elementsEntered++;
        if (elementsEntered === 2) {
          tableWrapper.removeEventListener("animationend", handleEnterEnd);
          tasksDayLabel.removeEventListener("animationend", handleEnterEnd);
        }
      }
      tableWrapper.addEventListener("animationend", handleEnterEnd);
      tasksDayLabel.addEventListener("animationend", handleEnterEnd);
    }
  }
  tableWrapper.addEventListener("animationend", handleExitEnd);
  tasksDayLabel.addEventListener("animationend", handleExitEnd);
}

/**
 * Cargar tareas para un día (0=domingo,...6=sábado)
 */
function loadTasksForDay(dayIndex) {
  const dayName = diasSemana[dayIndex];
  const tasksDayLabel = document.getElementById('tasks-day');
  tasksDayLabel.textContent = dayName.toUpperCase();

  const tbody = document.querySelector("#worker-table tbody");
  const headerRow = document.querySelector("#worker-table thead tr");
  tbody.innerHTML = "";
  headerRow.innerHTML = "";

  // Empleados visibles según paginación
  const startIndex = currentEmpPage * pageSize;
  const endIndex = startIndex + pageSize;
  const visibleTrabajadores = trabajadores.slice(startIndex, endIndex);

  // Cabeceras fijas: HORARIO + ACTIVIDAD
  const horarioTh = document.createElement("th");
  horarioTh.innerText = "Horario";
  headerRow.appendChild(horarioTh);

  const actividadTh = document.createElement("th");
  actividadTh.innerText = "Actividad";
  headerRow.appendChild(actividadTh);

  // Crear columnas para empleados visibles
  visibleTrabajadores.forEach(trabajador => {
    const th = document.createElement("th");
    const container = document.createElement("div");
    container.classList.add("worker-header");

    const img = document.createElement("img");
    img.src = `/web/images/${trabajador.imagen}`;
    img.alt = trabajador.nombre;

    const textContainer = document.createElement("div");
    textContainer.classList.add("worker-text");

    const nameSpan = document.createElement("span");
    nameSpan.innerText = trabajador.nombre;
    nameSpan.classList.add("worker-name");

    const roleSpan = document.createElement("span");
    roleSpan.innerText = trabajador.puesto;
    roleSpan.classList.add("worker-role");

    textContainer.appendChild(nameSpan);
    textContainer.appendChild(roleSpan);
    container.appendChild(img);
    container.appendChild(textContainer);
    th.appendChild(container);

    headerRow.appendChild(th);
  });

  // Si faltan columnas para llegar a 5, agregamos TH vacíos
  const missingCols = pageSize - visibleTrabajadores.length;
  for (let i = 0; i < missingCols; i++) {
    const thEmpty = document.createElement("th");
    thEmpty.innerText = "";
    headerRow.appendChild(thEmpty);
  }

  // Recolectar TODAS las actividades del día (de todos los empleados)
  let actividadesMap = {};
  trabajadores.forEach(trabajador => {
    const tareasDelDia = trabajador.tareas_asignadas[dayName] || [];
    tareasDelDia.forEach(t => {
      if (!actividadesMap[t.nombre]) {
        actividadesMap[t.nombre] = {
          nombre: t.nombre,
          descripcion: t.descripcion,
          hora: t.hora
        };
      } else {
        // Si la nueva hora es más temprana, actualizamos
        const storedHour = parseInt(actividadesMap[t.nombre].hora.split(":")[0], 10);
        const newHour = parseInt(t.hora.split(":")[0], 10);
        if (newHour < storedHour) {
          actividadesMap[t.nombre].hora = t.hora;
        }
      }
    });
  });

  // Ordenar actividades por hora
  const rowsData = Object.values(actividadesMap).sort((a, b) => {
    return parseInt(a.hora.split(":")[0]) - parseInt(b.hora.split(":")[0]);
  });

  // Generar filas
  rowsData.forEach(rowData => {
    const row = document.createElement("tr");

    // Columna HORARIO
    const horarioCell = document.createElement("td");
    horarioCell.innerText = rowData.hora ? rowData.hora + " hrs" : "-";
    row.appendChild(horarioCell);

    // Columna ACTIVIDAD
    const actividadCell = document.createElement("td");
    actividadCell.style.verticalAlign = "top";
    actividadCell.style.textAlign = "left";

    const nombreDiv = document.createElement("div");
    nombreDiv.classList.add("activity-name");
    nombreDiv.innerText = rowData.nombre;

    const descDiv = document.createElement("div");
    descDiv.classList.add("activity-desc");
    descDiv.innerText = rowData.descripcion;

    actividadCell.appendChild(nombreDiv);
    actividadCell.appendChild(descDiv);
    row.appendChild(actividadCell);

    // Celdas de cada empleado visible
    visibleTrabajadores.forEach(trabajador => {
      const cell = document.createElement("td");
      const tareasDelDia = trabajador.tareas_asignadas[dayName] || [];
      const tarea = tareasDelDia.find(t => t.nombre === rowData.nombre);
      if (tarea) {
        cell.classList.add(getStatusClass(tarea.estatus, tarea.hora));
        cell.innerText = "";
      } else {
        cell.innerText = "-";
      }
      row.appendChild(cell);
    });

    // Rellenar celdas vacías si faltan columnas
    for (let i = 0; i < missingCols; i++) {
      const cellEmpty = document.createElement("td");
      cellEmpty.innerText = "";
      row.appendChild(cellEmpty);
    }

    tbody.appendChild(row);
  });

  // Fusionar celdas de la columna "Horario" cuando tengan la misma hora
  mergeCells(0);

  // Mostrar/ocultar reloj si es hoy
  const realClockCols = document.querySelectorAll(".clock-col-real");
  const btnToday = document.getElementById('today-btn');
  const isToday = (dayIndex === new Date().getDay());

  if (isToday) {
    realClockCols.forEach(col => col.classList.remove("hidden"));
    btnToday.classList.add("hidden");
  } else {
    realClockCols.forEach(col => col.classList.add("hidden"));
    btnToday.classList.remove("hidden");
  }

  // Botones de paginación
  const prevEmpBtn = document.getElementById('prev-emp-page');
  const nextEmpBtn = document.getElementById('next-emp-page');
  const maxPage = Math.floor((trabajadores.length - 1) / pageSize);

  prevEmpBtn.disabled = (currentEmpPage <= 0);
  nextEmpBtn.disabled = (currentEmpPage >= maxPage);
}

/** Fusionar celdas de la columna X cuando tengan el mismo valor */
function mergeCells(columnIndex) {
  const tbody = document.querySelector("#worker-table tbody");
  const rows = Array.from(tbody.rows);
  let prevCell = null;
  let spanCount = 1;
  for (let i = 0; i < rows.length; i++) {
    let cell = rows[i].cells[columnIndex];
    if (prevCell && cell.innerText === prevCell.innerText) {
      spanCount++;
      prevCell.rowSpan = spanCount;
      cell.remove();
    } else {
      prevCell = cell;
      spanCount = 1;
    }
  }
}

/** Determina la clase CSS según estatus y hora */
function getStatusClass(estatus, hora) {
  const now = new Date();
  const currentHour = now.getHours();
  const taskHour = hora !== "-" ? parseInt(hora.split(":")[0], 10) : null;

  // Si la tarea no está completada y la hora ya pasó => overdue
  if ((estatus === 1 || estatus === 2 || estatus === 3) &&
      taskHour !== null && taskHour < currentHour) {
    return "status-overdue";
  }
  switch (estatus) {
    case 1: return "status-inprogress";
    case 2: return "status-todo";
    case 3: return "status-extras";
    case 0: return "status-done";
    default: return "";
  }
}

/** Actualizar el reloj (HH:MM:SS) */
function updateTime() {
  const now = new Date();
  let hour = now.getHours() || 24;
  let minutes = now.getMinutes().toString().padStart(2, '0');
  let seconds = now.getSeconds().toString().padStart(2, '0');

  document.documentElement.style.setProperty('--timer-hours', "'" + hour + "'");
  document.documentElement.style.setProperty('--timer-minutes', "'" + minutes + "'");
  document.documentElement.style.setProperty('--timer-seconds', "'" + seconds + "'");

  requestAnimationFrame(updateTime);
}
