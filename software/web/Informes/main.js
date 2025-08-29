// main.js
// ===============================================
import {
  obtenerEmpleados,
  obtenerBackup,
  crearMapaTareasRealizadas,
  getAllTasks
} from "./utils.js";
import { createEmpleadoCard } from "./empleados.js";

/* -------------------- Sesión ------------------- */
const usuario = JSON.parse(localStorage.getItem("loggedUser"));
if (!usuario || !["administrador", "empleado"].includes(usuario.role)) {
  window.location.href = "/inicio";
}

/* ---- Datos globales en memoria (una sola carga) */
let empleadosData = [];
let tareasRealizadasMap = {};

/* ----------------- ADMIN ----------------------- */
async function generarItinerarios() {
  const tarjetasContainer = document.getElementById("tarjetas-container");
  if (!tarjetasContainer) {
    console.error("No existe contenedor con ID 'tarjetas-container'.");
    return;
  }

  tarjetasContainer.style.display = "block";
  tarjetasContainer.innerHTML = "";

  empleadosData.forEach((empleado, i) => {
    const card = createEmpleadoCard(empleado, i);
    tarjetasContainer.appendChild(card);
  });

  // fade-in
  setTimeout(() => {
    document.getElementById("informes-content")?.classList.add("show");
  }, 300);
}

/* ---------------- EMPLEADO --------------------- */
async function mostrarPanelDerecho(empleadoId) {
  // Oculta panel izq
  document.getElementById("tarjetas-container")?.style.setProperty("display", "none");

  const empleado = empleadosData.find(e => e.id === empleadoId);
  if (!empleado) {
    console.error("No se encontró empleado con ID:", empleadoId);
    return;
  }

  mostrarTareasEmpleado(empleado);

  setTimeout(() => {
    document.getElementById("informes-content")?.classList.add("show");
  }, 300);
}

/* ------------- Al cargar la página ------------- */
document.addEventListener("DOMContentLoaded", async () => {
  try {
    // 1. Descargamos ambos JSON en paralelo
    const [emps, backup] = await Promise.all([
      obtenerEmpleados(),
      obtenerBackup()
    ]);

    empleadosData = emps;
    tareasRealizadasMap = crearMapaTareasRealizadas(backup);

    const { role, empleado_id } = usuario;

    if (role === "administrador") {
      await generarItinerarios();
    } else if (role === "empleado") {
      await mostrarPanelDerecho(parseInt(empleado_id, 10));
    }
  } catch (e) {
    console.error("Error inicializando aplicación:", e);
  }
});

/* ---------- Mostrar tareas tipo “card” --------- */
export function mostrarTareasEmpleado(empleado) {
  const calendarioContainer = document.getElementById("calendario-container");
  if (!calendarioContainer) return;

  calendarioContainer.style.display = "flex";
  calendarioContainer.innerHTML = "";
  calendarioContainer.classList.add("tasks-card");

  // Cabecera
  const headerDiv = document.createElement("div");
  headerDiv.classList.add("tasks-card-header");
  headerDiv.innerHTML = `<p>Tareas de ${empleado.nombre}</p>`;

  // Body
  const bodyDiv = document.createElement("div");
  bodyDiv.classList.add("tasks-card-body");

  // Todas las tareas desde empleados.json
  const allTasks = getAllTasks(empleado);

  /* -------- Mezclamos tareas realizadas -------- */
  const realizadasBackup = tareasRealizadasMap[empleado.id] || [];

  // Utilidad para filtrar y ordenar
  const byHora = (a, b) => parseHora(a.hora) - parseHora(b.hora);

  const tareasPend    = allTasks.filter(t => t.estatus === 1).sort(byHora);
  const tareasPorHacer= allTasks.filter(t => t.estatus === 2).sort(byHora);

  // 1) estatus 0 del JSON principal  2) + backup  3) quitar duplicados
  const tareasReal = [
    ...allTasks.filter(t => t.estatus === 0),
    ...realizadasBackup
  ].filter((t, i, arr) => arr.findIndex(x => x.id === t.id) === i)
   .sort(byHora);

  const tareasExtra   = allTasks.filter(t => t.estatus === 3).sort(byHora);

  /* -------- Render de secciones ---------------- */
  bodyDiv.appendChild(crearSeccionTareas("Tareas Pendientes",  tareasPend));
  bodyDiv.appendChild(crearSeccionTareas("Tareas por Realizar", tareasPorHacer));
  bodyDiv.appendChild(crearSeccionTareas("Tareas Realizadas",  tareasReal));
  bodyDiv.appendChild(crearSeccionTareas("Tareas Extras",      tareasExtra));

  calendarioContainer.appendChild(headerDiv);
  calendarioContainer.appendChild(bodyDiv);
}

/* ------------ utilidades internas ------------- */
function parseHora(horaStr) {
  if (!horaStr) return 999999;
  const [hh, mm = "0"] = horaStr.split(":");
  return parseInt(hh, 10) * 60 + parseInt(mm, 10);
}

function crearSeccionTareas(titulo, lista) {
  const sectionWrapper = document.createElement("div");

  const h2 = document.createElement("h2");
  h2.classList.add("tasks-section-title");
  h2.textContent = titulo;
  sectionWrapper.appendChild(h2);

  if (!lista.length) {
    const pVacio = document.createElement("p");
    pVacio.classList.add("tasks-empty");
    pVacio.textContent = "No hay tareas en esta sección.";
    sectionWrapper.appendChild(pVacio);
    return sectionWrapper;
  }

  // Agrupar por día
  const tareasPorDia = {};
  lista.forEach(t => {
    const dia = t.dia || "Sin día";
    (tareasPorDia[dia] ||= []).push(t);
  });

  for (const [dia, tareasDelDia] of Object.entries(tareasPorDia)) {
    const h3 = document.createElement("h3");
    h3.classList.add("tasks-day-title");
    h3.textContent = `${dia}:`;
    sectionWrapper.appendChild(h3);

    const ul = document.createElement("ul");
    ul.classList.add("tasks-list");

    tareasDelDia.forEach(t => {
      const li = document.createElement("li");

      const spanName  = Object.assign(document.createElement("span"), { className: "task-name",  textContent: t.nombre });
      const spanHour  = Object.assign(document.createElement("span"), { className: "task-hour",  textContent: t.hora || "-" });
      const spanExtra = Object.assign(document.createElement("span"), { className: "task-extra", textContent: t.descripcion || "" });

      li.append(spanName, spanHour, spanExtra);
      ul.appendChild(li);
    });

    sectionWrapper.appendChild(ul);
  }

  return sectionWrapper;
}
