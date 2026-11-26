# Tickets escalados a Galileo

Página de consulta con el tiempo a solución de los tickets escalados en el canal de Slack
**#support-stream-aligned-teams**, por analista de Tech y por periodo (día, semana, mes, Q, semestre y año).

Página: https://guillermovillanueva-source.github.io/tickets-escalados-galileo/

## Cómo funciona

1. La Action **Actualizar datos** (`.github/workflows/actualizar-datos.yml`) corre todos los días a las 6:00 am (hora del centro de México),
   o a mano desde la pestaña **Actions → Actualizar datos → Run workflow**.
2. `scripts/fetch_data.py` baja:
   - de **ClickUp**, las listas Customer Journey, Foundational Services y Reporte de Incidentes/Problemas Service Desk
     (espacio Mesa de Ayuda Galileo), con el historial de estados de cada ticket;
   - de **Slack**, los mensajes principales del canal desde el 1 de enero de 2025, para saber qué tickets se escalaron ahí.
3. Guarda todo en `docs/data.json`, y GitHub Pages publica `docs/`.
4. `docs/index.html` hace los cálculos en el navegador: filtros, medianas, gráficas y tablas.

## Configuración (una sola vez)

En **Settings → Secrets and variables → Actions → New repository secret** agrega:

| Secreto | Qué es |
|---|---|
| `CLICKUP_TOKEN` | Token personal de ClickUp (`pk_...`), en ClickUp → Settings → Apps → API Token. Debe tener acceso al espacio Mesa de Ayuda Galileo. |
| `SLACK_TOKEN` | Token de bot (`xoxb-...`) de una app de Slack con el permiso `channels:history` (o `groups:history` si el canal es privado). El bot tiene que estar invitado al canal #support-stream-aligned-teams. |

Después corre la Action a mano una vez para que aparezcan los datos.

## Reglas del cálculo

- **Qué tickets entran:** los que tienen un link de ClickUp en un mensaje principal del canal (no en respuestas de hilo).
- **Tiempo a solución:** desde que se crea el ticket hasta que pasa a *review*; si nunca pasó por *review*, hasta que se cerró.
  Son horas de calendario.
- **Cierres masivos:** si se cerraron 5 o más tickets en la misma hora y el ticket no pasó por *review*, queda fuera de las medianas.
- **Analistas:** solo los 32 analistas de desarrollo de Tech, definidos por su id de ClickUp en `docs/index.html` (constante `ANALISTAS`).

## Aviso

El sitio es público: cualquiera con el link ve los nombres de los analistas, los títulos de los tickets y sus tiempos.
