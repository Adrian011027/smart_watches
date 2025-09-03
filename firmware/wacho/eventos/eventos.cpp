#include <vector>

#include "eventos.h"
#include "funciones/control_carga.h"
#include "funciones/control_tareas/control_tareas.h"
#include "eventos/var_pantalla.h"
#include "funciones/control_tareas/var_tareas.h"

void marcarTareaCompletada(std::vector<Tarea> &listaTareas, lv_obj_t *boton, lv_obj_t *contenedor, lv_obj_t *contenedorPrincipal);

void AbrirTareasExtras(lv_event_t *e)
{
    lv_scr_load(ui_PantallaTareasExtras);                                // 🔹 Cambia a la pantalla de Tareas Extras
    lv_obj_set_parent(ui_ContInformacionReloj, ui_PantallaTareasExtras); // 🔹 Mueve el AppBar a la nueva pantalla
    lv_obj_set_parent(ui_ContAnimacionDeCarga, ui_PantallaTareasExtras); // 🔹 Mueve el AppBar a la nueva pantalla
}

void AbrirPendientes(lv_event_t *e)
{
    lv_scr_load(ui_PantallaPendientes);                                // 🔹 Cambia a la pantalla de Pendientes
    lv_obj_set_parent(ui_ContInformacionReloj, ui_PantallaPendientes); // 🔹 Mueve el AppBar a la nueva pantalla
    lv_obj_set_parent(ui_ContAnimacionDeCarga, ui_PantallaPendientes); // 🔹 Mueve el AppBar a la nueva pantalla
}

void completarTarea(lv_event_t *e)
{
    marcarTareaCompletada(listaTareas, ui_BtnCompletarTarea, ui_ContPContenido, ui_ContPanelPrincial);
}

void completarTareaExtra(lv_event_t *e)
{
    marcarTareaCompletada(listaTareasExtras, ui_BtnCompletarTareaExtra, ui_ContTEContenido, ui_ContTareasExtras);
}

void marcarTareaCompletada(std::vector<Tarea> &listaTareas, lv_obj_t *boton, lv_obj_t *contenedor, lv_obj_t *contenedorPrincipal)
{
    if (!pantallaEncendida)
        return;

    for (auto &t : listaTareas)
    {
        if (strcmp(t.estado.c_str(), "En Progreso") == 0)
        {
            Serial.printf("✅ Tarea completada: %s\n", t.nombre.c_str());

            t.estado = "Completado";    
            lv_obj_set_style_text_color(t.label, obtenerColorEstado("Completado"), 0);
            actualizarEstadoBotonYContenedor(listaTareas, boton, contenedor, contenedorPrincipal);

            // 📡 Enviar al servidor por WebSocket
            JsonDocument doc;

            // ✅ Detectar si es tarea extra
            bool esTareaExtra = (&listaTareas == &listaTareasExtras);
            doc["accion"] = esTareaExtra ? "tarea_extra" : "tarea_terminada";
            
            doc["Tarea"] = t.nombre;
            doc["TaskID"] = t.taskId;
            
            // ✅ Siempre usar el empleado asignado al reloj actual
            doc["Empleado"] = t.idEmpleado;
            doc["uuid"] = loggin.Uuid;

            String jsonString;
            serializeJson(doc, jsonString);
            webSocket.sendTXT(jsonString);
            Serial.printf("📤 Mensaje enviado: %s\n", jsonString.c_str());

            return;
        }
    }

    Serial.println("⚠️ No hay tareas en progreso para completar.");
}
