# App Flask - Simulador Lagun Aro

Aplicacion web para simular la concesion de prestamos de automocion y consultar el historial
de simulaciones guardadas.

## Requisitos
- Python 3.10+
- Entorno probado con `Python 3.12.12`.

## Instalacion
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion
```bash
python app.py
```

Abre `http://127.0.0.1:5000` en el navegador.

## Estructura (scripts y recursos)
```text
Flask/
+- app.py                         (servidor Flask, rutas, carga modelos y escritura en DB)
+- bbdd.DB                        (base de datos SQLite con simulaciones)
+- requirements.txt               (dependencias de la app)
+- README.md                      (este documento)
+- modelos_pkl/
??  +- clustering/
??  ??  +- modelo_clustering.pkl    (modelo de clustering)
??  ??  +- scaler_clustering.pkl    (escalado de variables)
??  ??  +- feature_names_clustering.pkl (orden de features)
??  ??  +- config_clustering.json   (parametros/metadata)
??  +- objetivo_3/
??  ??  +- modelo_reglog.pkl        (modelo de impago)
??  +- objetivo_4/
??  ??  +- modelo_final.pkl         (modelo de coste esperado)
??  ??  +- scaler_final.pkl         (escalado del objetivo 4)
??  ??  +- feature_names.pkl        (features usadas por el modelo)
??  ??  +- config_produccion.json   (configuracion de produccion)
??  ??  +- resumen_ejecutivo_obj4_amplio.json (resumen)
+- static/
Â¦  +- css/styles.css              (estilos)
Â¦  +- js/aurora.js                (animaciones/efectos)
Â¦  +- imagenes/imagenlagunaro.png (logo/imagen)
+- templates/
   +- base.html                   (layout base + menu y loaders)
   +- index.html                  (landing)
   +- identificacion.html         (formulario de nombre y DNI)
   +- simulador.html              (formulario principal)
   +- formulario_terminado.html   (resultado de simulacion)
   +- historial.html              (busqueda por DNI)
   +- tabla.html                  (detalle de una simulacion)
   +- historial_todos.html        (vista admin con todas las simulaciones)
```

## Flujo interno (que pasa al clicar cada boton)
1. **Menu/Inicio**: enlaces a `GET /`, `GET /identificacion` y `GET /historial`. Se muestra un loader global (JS en `base.html`) antes de navegar.
2. **Continuar (Identificacion)**: `POST /identificacion`. Guarda `nombre` y `dni` en sesion y redirige a `GET /simulador`.
3. **Simular (Formulario principal)**: `POST /simulador`. Proceso interno: `preparar_entrada` -> `predecir_probabilidad_impago` (base) -> `predecir_cluster` -> `predecir_probabilidad_impago` (final) -> decision de prestamo -> evaluacion de ratios -> insercion en SQLite -> guardado en sesion -> redirect a `GET /formulario_terminado`.
4. **Limpiar (Formulario principal)**: resetea el formulario en el navegador.
5. **Buscar (Historial)**: `POST /historial`. Si el DNI coincide con el token admin configurado en `app.py`, redirige a `GET /historial/todos`. Si no, redirige a `GET /historial/<dni>`.
6. **Ver mi simulacion**: `GET /historial/<dni>` con el detalle de la simulacion guardada.
7. **Volver / Nueva busqueda**: enlaces directos a `GET /` o `GET /historial`.

## Datos y recursos utilizados
- **Base de datos**: `bbdd.DB` (SQLite) con la tabla `simulaciones`. Columnas: `dni`, `nombre`, `edad`, `ingresos`, `monto_inicial`, `scoring_crediticio`, `meses_empleo`, `num_creditos`, `ratio_interes`, `duracion`, `ratio_deuda_ingresos`, `estudios`, `posesion_hipoteca`, `personas_cargo`, `fiador`, `jornada`, `estado_civil`, `probabilidad_impago`, `cluster_kmeans`, `decision_prestamo`, `created_at`.
- **Modelos de clustering**: `modelos_pkl/clustering/*` (modelo + scaler + features).
- **Modelo de impago**: `app.py` espera `modelos_pkl/objetivo_3/modelo_reglog.pkl` y usa `modelos_pkl/objetivo_4/feature_names.pkl` para el orden de features.
- **Plantillas HTML**: en `templates/` para renderizar las vistas.
- **Recursos estaticos**: CSS, JS e imagenes en `static/`.
- **CDN externos**: GSAP y ScrollTrigger (incluidos en `base.html`).
- **Graficos**: la app no genera graficos; solo muestra resultados y mensajes en pantalla.

## Notas
- La app usa `joblib` si esta disponible y hace fallback a `pickle`.
- El loader global y el overlay del simulador se activan con JS (ver `base.html` y `simulador.html`).
- `bbdd.DB` puede contener datos sensibles si se usa con datos reales. No compartir en repositorios publicos.
- Para entrar en modo administrador, escribe `administrador_patricia` en el campo DNI del historial.

## Creditos
- Los elementos graficos que se han utilizado en este Flask se han obtenido de estas webs con finalidades educativas:
https://reactbits.dev
https://jitter.video
https://uiverse.io
