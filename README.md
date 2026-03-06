# Modelización Predictiva y Sistemas de Amortización para Préstamos de Automoción
Repositorio del RETO 07 - **Grupo Naranja** para la empresa **Lagun Aro**.

## Descripción
Proyecto universitario para analizar préstamos de automoción, **segmentar** la cartera mediante clustering y **estimar la probabilidad de impago**, además de modelar el coste esperado del seguro de protección de pagos y generar visualizaciones.

## Autores
- Grupo Naranja

## Requisitos e instalación
El entorno se instala con el comando indicado en `indicaciones_entorno_virtual_conda.txt`.
Entorno probado con `Python 3.12.12`.

## Ejecución
Los notebooks se ejecutan en **orden del 1 al 6**. La aplicación Flask puede ejecutarse en cualquier momento.

1. **`01-Ingesta_Limpieza.ipynb`**  
   Carga el Excel original, filtra préstamos de automóvil, realiza limpieza y transformaciones básicas, y guarda `Datos/Transformados/df_limpio.csv`.

2. **`02-Clustering.ipynb`**  
   Segmenta la cartera con técnicas de clustering (KMeans, Agglomerative, DBSCAN, KPrototypes) y guarda `Datos/Transformados/clustering_final.csv`.

3. **`03-Objetivos_1-2.ipynb`**  
   Simula amortizaciones bajo sistemas francés y alemán usando `clustering_final.csv`.

4. **`04-Objetivo_3.ipynb`**  
   Estima la probabilidad de impago (clasificación) y genera `Datos/Transformados/Datos_Probabilidad_Impago.csv`.

5. **`05-Objetivo_4.ipynb`**  
   Predice el coste esperado del seguro de protección de pagos (regresión) a partir de `Datos_Probabilidad_Impago.csv`.

6. **`06-Visualizacion.ipynb`**  
   Genera gráficos y exporta PDFs en la carpeta `Graficos` (requiere `kaleido`).

## Datos de entrada
- Coloca los archivos de entrada en `Datos/Originales/`.
- La carpeta contiene un `.gitkeep` para mantenerse en el repositorio.

## Resultados generados
- `Datos/Transformados/df_limpio.csv`
- `Datos/Transformados/clustering_final.csv`
- `Datos/Transformados/Datos_Probabilidad_Impago.csv`
- Gráficos en `Graficos/`

La carpeta `Datos/Transformados/` está vacía en el repositorio y contiene un `.gitkeep`. Al ejecutar los scripts, los resultados se van guardando ahí.

## Estructura del repositorio
```text
25-26_R07_NARANJA/
├─ Datos/
│  ├─ Originales/            (inputs; incluye .gitkeep)
│  └─ Transformados/         (df_limpio.csv, clustering_final.csv, Datos_Probabilidad_Impago.csv)
├─ Flask/
│  ├─ modelos_pkl/
│  ├─ static/
│  ├─ templates/
│  ├─ app.py
│  ├─ bbdd.DB
│  ├─ README.md              (documentación específica de la app Flask)
│  └─ requirements.txt
├─ Graficos/                 (salida de visualizaciones en PDF)
├─ 01-Ingesta_Limpieza.ipynb
├─ 02-Clustering.ipynb
├─ 03-Objetivos_1-2.ipynb
├─ 04-Objetivo_3.ipynb
├─ 05-Objetivo_4.ipynb
├─ 06-Visualizacion.ipynb
├─ entorno_RETO07.yml
└─ indicaciones_entorno_virtual_conda.txt
```

No hemos encontrado valores faltantes ni outliers, por eso no hemos utilizado procesamiento.py aunque hemos implementado algunas funciones.
