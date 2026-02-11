from flask import Flask, redirect, render_template, request, session, url_for
import os
import sqlite3

app = Flask(__name__)
app.secret_key = "lagun-aro-simulador"


DB_PATH = os.path.join(os.path.dirname(__file__), "bbdd.DB")


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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def normalize_dni(value):
    if value is None:
        return ""
    return value.strip().upper()


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

    payload = {
        "edad": request.form.get("Edad"),
        "ingresos": request.form.get("Ingresos"),
        "monto_inicial": request.form.get("Monto_Inicial"),
        "scoring_crediticio": request.form.get("Scoring_Crediticio"),
        "meses_empleo": request.form.get("Meses_Empleo"),
        "num_creditos": request.form.get("Num_Creditos"),
        "ratio_interes": request.form.get("Ratio_Interes"),
        "duracion": request.form.get("Duracion"),
        "ratio_deuda_ingresos": request.form.get("Ratio_Deuda_Ingresos"),
        "estudios": request.form.get("Estudios"),
        "posesion_hipoteca": request.form.get("Posesion_Hipoteca"),
        "personas_cargo": request.form.get("Personas_Cargo"),
        "fiador": request.form.get("Fiador"),
        "jornada": request.form.get("Jornada"),
        "estado_civil": request.form.get("Estado_Civil"),
    }

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO simulaciones (
                dni, nombre, edad, ingresos, monto_inicial, scoring_crediticio,
                meses_empleo, num_creditos, ratio_interes, duracion,
                ratio_deuda_ingresos, estudios, posesion_hipoteca,
                personas_cargo, fiador, jornada, estado_civil
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                dni,
                nombre,
                payload["edad"],
                payload["ingresos"],
                payload["monto_inicial"],
                payload["scoring_crediticio"],
                payload["meses_empleo"],
                payload["num_creditos"],
                payload["ratio_interes"],
                payload["duracion"],
                payload["ratio_deuda_ingresos"],
                payload["estudios"],
                payload["posesion_hipoteca"],
                payload["personas_cargo"],
                payload["fiador"],
                payload["jornada"],
                payload["estado_civil"],
            ),
        )

    session["last_dni"] = dni
    return redirect(url_for("formulario_terminado"))


@app.route("/formulario_terminado")
def formulario_terminado():
    dni = session.get("last_dni")
    return render_template("formulario_terminado.html", title="Formulario completado", dni=dni)


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
    return render_template(
        "tabla.html",
        title="Historial de simulación",
        registro=row,
        dni=dni_norm,
    )


init_db()


if __name__ == "__main__":
    app.run(debug=True)
