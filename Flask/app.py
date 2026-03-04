from flask import Flask, redirect, render_template, request, session, url_for
import os
import pickle
import sqlite3
import pandas as pd

try:
    import joblib
except Exception:
    joblib = None

app = Flask(__name__)
app.secret_key = "lagun-aro-simulador"


BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "bbdd.DB")
ADMIN_TOKEN = "administrador_patricia"

MODELO_CLUSTERING_PATH = os.path.join(
    BASE_DIR, "modelos_pkl", "clustering", "modelo_clustering.pkl"
)
SCALER_CLUSTERING_PATH = os.path.join(
    BASE_DIR, "modelos_pkl", "clustering", "scaler_clustering.pkl"
)
FEATURES_CLUSTERING_PATH = os.path.join(
    BASE_DIR, "modelos_pkl", "clustering", "feature_names_clustering.pkl"
)

MODELO_IMPAGO_PATH = os.path.join(
    BASE_DIR, "modelos_pkl", "objetivo_3", "modelo_reglog.pkl"
)
FEATURES_OBJ4_PATH = os.path.join(
    BASE_DIR, "modelos_pkl", "objetivo_4", "feature_names.pkl"
)

_modelo_clustering = None
_scaler_clustering = None
_features_clustering = None
_modelo_impago = None
_features_impago = None


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS simulaciones (
                dni TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                edad INTEGER,
                ingresos REAL,
                monto_inicial REAL,
                scoring_crediticio INTEGER,
                meses_empleo INTEGER,
                num_creditos INTEGER,
                ratio_interes REAL,
                duracion INTEGER,
                ratio_deuda_ingresos REAL,
                estudios TEXT,
                posesion_hipoteca TEXT,
                personas_cargo INTEGER,
                fiador TEXT,
                jornada TEXT,
                estado_civil TEXT,
                probabilidad_impago REAL,
                cluster_kmeans INTEGER,
                decision_prestamo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        asegurar_columnas(conn)


def asegurar_columnas(conn):
    columnas = {
        row[1] for row in conn.execute("PRAGMA table_info(simulaciones)").fetchall()
    }
    if "probabilidad_impago" not in columnas:
        conn.execute("ALTER TABLE simulaciones ADD COLUMN probabilidad_impago REAL")
    if "cluster_kmeans" not in columnas:
        conn.execute("ALTER TABLE simulaciones ADD COLUMN cluster_kmeans INTEGER")
    if "decision_prestamo" not in columnas:
        conn.execute("ALTER TABLE simulaciones ADD COLUMN decision_prestamo TEXT")


def normalize_dni(value):
    if value is None:
        return ""
    return value.strip().upper()


def es_admin():
    return session.get("es_admin") is True


def cargar_pickle(path):
    if joblib is not None:
        try:
            return joblib.load(path)
        except Exception:
            pass
    with open(path, "rb") as archivo:
        try:
            return pickle.load(archivo)
        except Exception:
            archivo.seek(0)
            return pickle.load(archivo, encoding="latin1")


def obtener_modelo_clustering():
    global _modelo_clustering
    if _modelo_clustering is None:
        _modelo_clustering = cargar_pickle(MODELO_CLUSTERING_PATH)
    return _modelo_clustering


def obtener_scaler_clustering():
    global _scaler_clustering
    if _scaler_clustering is None:
        _scaler_clustering = cargar_pickle(SCALER_CLUSTERING_PATH)
    return _scaler_clustering


def obtener_features_clustering():
    global _features_clustering
    if _features_clustering is None:
        try:
            scaler = obtener_scaler_clustering()
            if hasattr(scaler, "feature_names_in_"):
                _features_clustering = list(scaler.feature_names_in_)
            else:
                modelo = obtener_modelo_clustering()
                if hasattr(modelo, "feature_names_in_"):
                    _features_clustering = list(modelo.feature_names_in_)
                else:
                    _features_clustering = cargar_pickle(FEATURES_CLUSTERING_PATH)
        except Exception:
            _features_clustering = cargar_pickle(FEATURES_CLUSTERING_PATH)
    return _features_clustering


def obtener_modelo_impago():
    global _modelo_impago
    if _modelo_impago is None:
        _modelo_impago = cargar_pickle(MODELO_IMPAGO_PATH)
    return _modelo_impago


def obtener_features_impago():
    global _features_impago
    if _features_impago is None:
        modelo = obtener_modelo_impago()
        if hasattr(modelo, "feature_names_in_"):
            _features_impago = list(modelo.feature_names_in_)
        else:
            _features_impago = cargar_pickle(FEATURES_OBJ4_PATH)
    return _features_impago


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def evaluar_ratio_interes(valor):
    if valor is None:
        return None
    if 19 <= valor <= 25:
        return {
            "categoria": "Mucho",
            "significancia": "Riesgo muy alto",
            "mejorable": True,
            "mensaje": (
                "El nivel de interés es excesivo y afecta significativamente la "
                "capacidad de pago. Se recomienda evaluar alternativas como "
                "refinanciación o consolidación de deuda."
            ),
        }
    if 13 <= valor <= 18.9:
        return {
            "categoria": "Mucho-Medio",
            "significancia": "Riesgo alto",
            "mejorable": True,
            "mensaje": (
                "El costo financiero es elevado y puede impactar el flujo de caja. "
                "Conviene analizar opciones para mejorar las condiciones de financiamiento."
            ),
        }
    if 7 <= valor <= 12.9:
        return {
            "categoria": "Medio-Bajo",
            "significancia": "Riesgo moderado",
            "mejorable": True,
            "mensaje": (
                "La tasa es manejable dentro de parámetros razonables, aunque podría "
                "optimizarse para mejorar la estructura financiera."
            ),
        }
    if 2 <= valor <= 6.9:
        return {
            "categoria": "Bajo",
            "significancia": "Riesgo bajo",
            "mejorable": False,
            "mensaje": (
                "El nivel de interés es favorable y sostenible, reflejando una "
                "estructura de financiamiento saludable."
            ),
        }
    return {
        "categoria": "Fuera de rango",
        "significancia": "Sin clasificación",
        "mejorable": True,
        "mensaje": "El ratio de interés está fuera del rango esperado (2% – 25%).",
    }


def evaluar_scoring_crediticio(valor):
    if valor is None:
        return None
    if 750 <= valor <= 849:
        return {
            "categoria": "Mucho",
            "significancia": "Perfil excelente",
            "mejorable": False,
            "mensaje": (
                "Presenta un historial crediticio sólido, con alta probabilidad de "
                "aprobación y acceso a condiciones preferenciales."
            ),
        }
    if 650 <= valor <= 749:
        return {
            "categoria": "Mucho-Medio",
            "significancia": "Perfil bueno",
            "mejorable": False,
            "mensaje": (
                "Mantiene un comportamiento crediticio adecuado y acceso competitivo "
                "a financiamiento."
            ),
        }
    if 550 <= valor <= 649:
        return {
            "categoria": "Medio-Bajo",
            "significancia": "Perfil en observación",
            "mejorable": True,
            "mensaje": (
                "Evidencia riesgo moderado. Podría enfrentar condiciones más "
                "restrictivas o mayores tasas."
            ),
        }
    if 300 <= valor <= 549:
        return {
            "categoria": "Bajo",
            "significancia": "Perfil riesgoso",
            "mejorable": True,
            "mensaje": (
                "Representa un alto riesgo crediticio, con baja probabilidad de "
                "aprobación o condiciones desfavorables. Se recomienda fortalecer el "
                "historial antes de nuevas solicitudes."
            ),
        }
    return {
        "categoria": "Fuera de rango",
        "significancia": "Sin clasificación",
        "mejorable": True,
        "mensaje": "El scoring crediticio está fuera del rango esperado (300 – 849).",
    }


def evaluar_ratio_deuda_ingresos(valor):
    if valor is None:
        return None
    if 0.45 <= valor <= 0.55:
        return {
            "categoria": "Mucho",
            "significancia": "Alto endeudamiento",
            "mejorable": True,
            "mensaje": (
                "El nivel de deuda respecto a los ingresos es elevado y podría "
                "comprometer la estabilidad financiera."
            ),
        }
    if 0.35 <= valor <= 0.449:
        return {
            "categoria": "Mucho-Medio",
            "significancia": "Presión financiera significativa",
            "mejorable": True,
            "mensaje": (
                "La carga de deuda es considerable y puede limitar la capacidad de "
                "ahorro o asumir nuevas obligaciones."
            ),
        }
    if 0.20 <= valor <= 0.349:
        return {
            "categoria": "Medio-Bajo",
            "significancia": "Nivel saludable",
            "mejorable": False,
            "mensaje": (
                "La relación deuda-ingreso es adecuada y refleja un equilibrio "
                "financiero razonable."
            ),
        }
    if 0.10 <= valor <= 0.199:
        return {
            "categoria": "Bajo",
            "significancia": "Excelente control",
            "mejorable": False,
            "mensaje": (
                "La carga de deuda es baja en proporción a los ingresos, lo que "
                "indica una sólida capacidad financiera."
            ),
        }
    return {
        "categoria": "Fuera de rango",
        "significancia": "Sin clasificación",
        "mejorable": True,
        "mensaje": "El ratio deuda/ingresos está fuera del rango esperado (0.10 – 0.55).",
    }


def preparar_entrada(form):
    jornada_desempleado = to_int(form.get("Tipo_Jornada_Laboral_Desempleado"))
    jornada_completa = to_int(form.get("Tipo_Jornada_Laboral_Jornada completa"))
    jornada_parcial = to_int(form.get("Tipo_Jornada_Laboral_Tiempo parcial"))
    estado_divorciado = to_int(form.get("Estado_Civil_Divorciado"))
    estado_soltero = to_int(form.get("Estado_Civil_Soltero"))
    jornada = form.get("Jornada")
    estado_civil = form.get("Estado_Civil")

    if jornada is None:
        if jornada_desempleado:
            jornada = "desempleado"
        elif jornada_completa:
            jornada = "jornada completa"
        elif jornada_parcial:
            jornada = "jornada parcial"
        else:
            jornada = "autonomo"

    if estado_civil is None:
        if estado_divorciado:
            estado_civil = "divorciado"
        elif estado_soltero:
            estado_civil = "soltero"
        else:
            estado_civil = "casado"

    return {
        "Edad": to_int(form.get("Edad")),
        "Ingresos": to_float(form.get("Ingresos")),
        "Monto_Inicial": to_float(form.get("Monto_Inicial")),
        "Scoring_Crediticio": to_int(form.get("Scoring_Crediticio")),
        "Meses_Empleo": to_int(form.get("Meses_Empleo")),
        "Num_Creditos": to_int(form.get("Num_Creditos")),
        "Ratio_Interes": to_float(form.get("Ratio_Interes")),
        "Duracion": to_int(form.get("Duracion")),
        "Ratio_Deuda_Ingresos": to_float(form.get("Ratio_Deuda_Ingresos")),
        "Estudios": form.get("Estudios"),
        "Posesion_Hipoteca": form.get("Posesion_Hipoteca"),
        "Personas_Cargo": to_int(form.get("Personas_Cargo")),
        "Fiador": form.get("Fiador"),
        "Jornada": jornada,
        "Estado_Civil": estado_civil,
        "Tipo_Jornada_Laboral_Desempleado": jornada_desempleado,
        "Tipo_Jornada_Laboral_Jornada completa": jornada_completa,
        "Tipo_Jornada_Laboral_Tiempo parcial": jornada_parcial,
        "Estado_Civil_Divorciado": estado_divorciado,
        "Estado_Civil_Soltero": estado_soltero,
    }


def mapear_estudios(valor):
    mapa = {
        "escolar": 0,
        "universitario": 1,
        "master": 2,
        "doctorado": 3,
    }
    return mapa.get(valor, 0)


def mapear_si_no(valor):
    return 1 if str(valor).strip().lower() == "si" else 0


def construir_fila_features(feature_names, entrada, prob_impago=None, cluster=None):
    fila = {nombre: 0 for nombre in feature_names}

    if "Edad" in fila:
        fila["Edad"] = entrada.get("Edad") or 0
    if "Ingresos" in fila:
        fila["Ingresos"] = entrada.get("Ingresos") or 0
    if "Monto_Inicial" in fila:
        fila["Monto_Inicial"] = entrada.get("Monto_Inicial") or 0
    if "Scoring_Crediticio" in fila:
        fila["Scoring_Crediticio"] = entrada.get("Scoring_Crediticio") or 0
    if "Meses_Empleo" in fila:
        fila["Meses_Empleo"] = entrada.get("Meses_Empleo") or 0
    if "Num_Creditos" in fila:
        fila["Num_Creditos"] = entrada.get("Num_Creditos") or 0
    if "Ratio_Interes" in fila:
        fila["Ratio_Interes"] = entrada.get("Ratio_Interes") or 0
    if "Duracion" in fila:
        fila["Duracion"] = entrada.get("Duracion") or 0
    if "Ratio_Deuda_Ingresos" in fila:
        fila["Ratio_Deuda_Ingresos"] = entrada.get("Ratio_Deuda_Ingresos") or 0
    if "Personas_Cargo" in fila:
        fila["Personas_Cargo"] = entrada.get("Personas_Cargo") or 0

    if "Estudios" in fila:
        fila["Estudios"] = mapear_estudios(entrada.get("Estudios"))
    if "Posesion_Hipoteca" in fila:
        fila["Posesion_Hipoteca"] = mapear_si_no(entrada.get("Posesion_Hipoteca"))
    if "Fiador" in fila:
        fila["Fiador"] = mapear_si_no(entrada.get("Fiador"))

    jornada = (entrada.get("Jornada") or "").lower()
    if "Tipo_Jornada_Laboral_Desempleado" in fila:
        if entrada.get("Tipo_Jornada_Laboral_Desempleado") is not None:
            fila["Tipo_Jornada_Laboral_Desempleado"] = (
                1 if entrada.get("Tipo_Jornada_Laboral_Desempleado") else 0
            )
        elif jornada == "desempleado":
            fila["Tipo_Jornada_Laboral_Desempleado"] = 1
    if "Tipo_Jornada_Laboral_Jornada completa" in fila:
        if entrada.get("Tipo_Jornada_Laboral_Jornada completa") is not None:
            fila["Tipo_Jornada_Laboral_Jornada completa"] = (
                1 if entrada.get("Tipo_Jornada_Laboral_Jornada completa") else 0
            )
        elif jornada == "jornada completa":
            fila["Tipo_Jornada_Laboral_Jornada completa"] = 1
    if "Tipo_Jornada_Laboral_Tiempo parcial" in fila:
        if entrada.get("Tipo_Jornada_Laboral_Tiempo parcial") is not None:
            fila["Tipo_Jornada_Laboral_Tiempo parcial"] = (
                1 if entrada.get("Tipo_Jornada_Laboral_Tiempo parcial") else 0
            )
        elif jornada == "jornada parcial":
            fila["Tipo_Jornada_Laboral_Tiempo parcial"] = 1

    estado_civil = (entrada.get("Estado_Civil") or "").lower()
    if "Estado_Civil_Divorciado" in fila:
        if entrada.get("Estado_Civil_Divorciado") is not None:
            fila["Estado_Civil_Divorciado"] = (
                1 if entrada.get("Estado_Civil_Divorciado") else 0
            )
        elif estado_civil == "divorciado":
            fila["Estado_Civil_Divorciado"] = 1
    if "Estado_Civil_Soltero" in fila:
        if entrada.get("Estado_Civil_Soltero") is not None:
            fila["Estado_Civil_Soltero"] = (
                1 if entrada.get("Estado_Civil_Soltero") else 0
            )
        elif estado_civil == "soltero":
            fila["Estado_Civil_Soltero"] = 1

    if "Impago" in fila:
        fila["Impago"] = prob_impago if prob_impago is not None else 0
    if "Prima" in fila:
        fila["Prima"] = 0

    if "Cluster_KMeans" in fila:
        fila["Cluster_KMeans"] = cluster if cluster is not None else 0
    if "Cluster_Jerarquico" in fila:
        fila["Cluster_Jerarquico"] = 0
    if "Cluster_DBSCAN" in fila:
        fila["Cluster_DBSCAN"] = 0

    return fila


def ajustar_a_features_modelo(df, modelo):
    if hasattr(modelo, "feature_names_in_"):
        expected = list(modelo.feature_names_in_)
        return df.reindex(columns=expected, fill_value=0)
    return df


def ajustar_a_features_scaler(df, scaler, modelo=None):
    if hasattr(scaler, "feature_names_in_"):
        expected = list(scaler.feature_names_in_)
        return df.reindex(columns=expected, fill_value=0)
    if modelo is not None and hasattr(modelo, "feature_names_in_"):
        expected = list(modelo.feature_names_in_)
        return df.reindex(columns=expected, fill_value=0)
    return df


def predecir_probabilidad_impago(entrada, cluster_kmeans=0):
    modelo = obtener_modelo_impago()
    features = obtener_features_impago()
    fila = construir_fila_features(features, entrada, cluster=cluster_kmeans)
    df_features = pd.DataFrame([fila], columns=features)
    df_features = ajustar_a_features_modelo(df_features, modelo)
    return float(modelo.predict_proba(df_features)[:, 1][0])


def predecir_cluster(entrada, prob_impago):
    modelo = obtener_modelo_clustering()
    scaler = obtener_scaler_clustering()
    features = obtener_features_clustering()

    fila = construir_fila_features(features, entrada, prob_impago=prob_impago)
    df_features = pd.DataFrame([fila], columns=features)
    df_features = ajustar_a_features_scaler(df_features, scaler, modelo=modelo)
    datos_escalados = scaler.transform(df_features)
    return int(modelo.predict(datos_escalados)[0])


@app.route("/")
def index():
    return render_template("index.html", title="Lagun Aro · Simulador")


@app.route("/identificacion", methods=["GET", "POST"])
def identificacion():
    if request.method == "POST":
        nombre = request.form.get("nombre_completo", "").strip()
        dni = normalize_dni(request.form.get("dni"))
        if not nombre or not dni:
            return render_template(
                "identificacion.html",
                title="Identificación",
                error="Completa el nombre y el DNI para continuar.",
            )
        session["nombre_completo"] = nombre
        session["dni"] = dni
        session["es_admin"] = False
        return redirect(url_for("simulador"))
    return render_template("identificacion.html", title="Identificación")


@app.route("/simulador")
def simulador():
    if not session.get("dni"):
        return redirect(url_for("identificacion"))
    return render_template("simulador.html", title="Simula tu concesión del préstamo")


@app.route("/simulador", methods=["POST"])
def simulador_post():
    dni = normalize_dni(session.get("dni"))
    nombre = session.get("nombre_completo", "").strip()
    if not dni or not nombre:
        return redirect(url_for("identificacion"))

    entrada = preparar_entrada(request.form)

    prob_impago_base = predecir_probabilidad_impago(entrada, cluster_kmeans=0)
    cluster_kmeans = predecir_cluster(entrada, prob_impago_base)
    probabilidad_impago = predecir_probabilidad_impago(
        entrada, cluster_kmeans=cluster_kmeans
    )
    decision_prestamo = (
        "Préstamo concedido"
        if probabilidad_impago <= 0.30
        else "Préstamo rechazado"
    )
    mensajes_metricas = [
        {
            "titulo": "Ratio de interés",
            "valor": entrada.get("Ratio_Interes"),
            **(evaluar_ratio_interes(entrada.get("Ratio_Interes")) or {}),
        },
        {
            "titulo": "Scoring crediticio",
            "valor": entrada.get("Scoring_Crediticio"),
            **(evaluar_scoring_crediticio(entrada.get("Scoring_Crediticio")) or {}),
        },
        {
            "titulo": "Ratio deuda / ingresos",
            "valor": entrada.get("Ratio_Deuda_Ingresos"),
            **(
                evaluar_ratio_deuda_ingresos(
                    entrada.get("Ratio_Deuda_Ingresos")
                )
                or {}
            ),
        },
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO simulaciones (
                dni, nombre, edad, ingresos, monto_inicial, scoring_crediticio,
                meses_empleo, num_creditos, ratio_interes, duracion,
                ratio_deuda_ingresos, estudios, posesion_hipoteca,
                personas_cargo, fiador, jornada, estado_civil,
                probabilidad_impago, cluster_kmeans, decision_prestamo
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                dni,
                nombre,
                entrada["Edad"],
                entrada["Ingresos"],
                entrada["Monto_Inicial"],
                entrada["Scoring_Crediticio"],
                entrada["Meses_Empleo"],
                entrada["Num_Creditos"],
                entrada["Ratio_Interes"],
                entrada["Duracion"],
                entrada["Ratio_Deuda_Ingresos"],
                entrada["Estudios"],
                entrada["Posesion_Hipoteca"],
                entrada["Personas_Cargo"],
                entrada["Fiador"],
                entrada["Jornada"],
                entrada["Estado_Civil"],
                probabilidad_impago,
                cluster_kmeans,
                decision_prestamo,
            ),
        )

    session["last_dni"] = dni
    session["decision_prestamo"] = decision_prestamo
    session["probabilidad_impago"] = probabilidad_impago
    session["cluster_kmeans"] = cluster_kmeans
    session["mensajes_metricas"] = mensajes_metricas
    return redirect(url_for("formulario_terminado"))


@app.route("/formulario_terminado")
def formulario_terminado():
    dni = session.get("last_dni")
    return render_template(
        "formulario_terminado.html",
        title="Formulario completado",
        dni=dni,
        decision_prestamo=session.get("decision_prestamo"),
        probabilidad_impago=session.get("probabilidad_impago"),
        cluster_kmeans=session.get("cluster_kmeans"),
        es_admin=es_admin(),
        mensajes_metricas=session.get("mensajes_metricas", []),
    )


@app.route("/historial", methods=["GET", "POST"])
def historial():
    if request.method == "POST":
        dni = normalize_dni(request.form.get("dni"))
        if not dni:
            return render_template(
                "historial.html",
                title="Historial",
                error="Introduce un DNI válido.",
            )
        if dni == ADMIN_TOKEN.upper():
            session["es_admin"] = True
            return redirect(url_for("historial_todos"))
        session["es_admin"] = False
        return redirect(url_for("historial_detalle", dni=dni))
    return render_template("historial.html", title="Historial")


@app.route("/historial/<dni>")
def historial_detalle(dni):
    dni_norm = normalize_dni(dni)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM simulaciones WHERE UPPER(dni) = ?",
            (dni_norm,),
        ).fetchone()
    mensajes_metricas = []
    if row:
        mensajes_metricas = [
            {
                "titulo": "Ratio de interés",
                "valor": row["ratio_interes"],
                **(evaluar_ratio_interes(row["ratio_interes"]) or {}),
            },
            {
                "titulo": "Scoring crediticio",
                "valor": row["scoring_crediticio"],
                **(evaluar_scoring_crediticio(row["scoring_crediticio"]) or {}),
            },
            {
                "titulo": "Ratio deuda / ingresos",
                "valor": row["ratio_deuda_ingresos"],
                **(evaluar_ratio_deuda_ingresos(row["ratio_deuda_ingresos"]) or {}),
            },
        ]
    probabilidad_impago = None
    cluster_kmeans = None
    decision_prestamo = None
    if row:
        probabilidad_impago = row["probabilidad_impago"]
        cluster_kmeans = row["cluster_kmeans"]
        decision_prestamo = row["decision_prestamo"]
        if decision_prestamo is None and probabilidad_impago is not None:
            decision_prestamo = (
                "Préstamo concedido"
                if probabilidad_impago <= 0.30
                else "Préstamo rechazado"
            )
    return render_template(
        "tabla.html",
        title="Historial de simulación",
        registro=row,
        dni=dni_norm,
        probabilidad_impago=probabilidad_impago,
        cluster_kmeans=cluster_kmeans,
        decision_prestamo=decision_prestamo,
        es_admin=es_admin(),
        mensajes_metricas=mensajes_metricas,
    )


@app.route("/historial/todos")
def historial_todos():
    if not es_admin():
        return redirect(url_for("historial"))
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM simulaciones ORDER BY created_at DESC"
        ).fetchall()
    return render_template(
        "historial_todos.html",
        title="Historial completo",
        registros=rows,
        es_admin=True,
    )


init_db()


if __name__ == "__main__":
    app.run(debug=True)
