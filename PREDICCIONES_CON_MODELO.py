# PREDICCIONES_CON_MODELO.py - VERSIÓN CORREGIDA
import sys
from pathlib import Path

import joblib
import pandas as pd
import tensorflow as tf


def _directorio_base_recursos():
    """Resolver ruta base tanto para script normal como para ejecutable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _buscar_recurso(nombre_archivo, requerido=True):
    """Buscar un recurso en rutas comunes de script/ejecutable PyInstaller."""
    base = _directorio_base_recursos()
    candidatos = [
        base / nombre_archivo,
        base / "_internal" / nombre_archivo,
        Path.cwd() / nombre_archivo,
    ]

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidatos.append(Path(meipass) / nombre_archivo)

    for ruta in candidatos:
        if ruta.exists():
            return ruta

    rutas_txt = "\n".join(f"- {r}" for r in candidatos)
    if requerido:
        raise FileNotFoundError(
            f"No se encontro el archivo requerido: {nombre_archivo}\n"
            f"Se busco en:\n{rutas_txt}"
        )

    return candidatos[0]


def cargar_modelo_y_scalers():
    """Cargar modelo y scalers con manejo de errores"""
    ruta_modelo_keras = _buscar_recurso('modelo_red_neuronal_agua.keras')
    ruta_modelo_h5 = _buscar_recurso('modelo_red_neuronal_agua.h5', requerido=False)
    ruta_scaler_x = _buscar_recurso('scaler_X.pkl')
    ruta_scaler_y = _buscar_recurso('scaler_y.pkl')

    try:
        # Intentar cargar el modelo en formato .keras (más moderno)
        model = tf.keras.models.load_model(ruta_modelo_keras)
        print("✅ Modelo cargado en formato .keras")
    except:
        try:
            # Intentar cargar en formato .h5 con opciones de compatibilidad
            model = tf.keras.models.load_model(
                ruta_modelo_h5,
                custom_objects=None,
                compile=False  # No compilar inicialmente
            )
            print("✅ Modelo cargado en formato .h5 (sin compilar)")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            return None, None, None

    try:
        # Cargar scalers
        scaler_X = joblib.load(ruta_scaler_x)
        scaler_y = joblib.load(ruta_scaler_y)
        print("✅ Scalers cargados correctamente")
        return model, scaler_X, scaler_y
    except Exception as e:
        print(f"❌ Error cargando scalers: {e}")
        return None, None, None


def predecir_desde_excel(ruta_entrada, ruta_salida='predicciones_finales.xlsx', verbose=True):
    """Ejecutar predicción completa usando un archivo Excel de entrada."""

    def log(msg):
        if verbose:
            print(msg)

    log("🔍 Iniciando proceso de predicción...")

    model, scaler_X, scaler_y = cargar_modelo_y_scalers()
    if model is None:
        raise RuntimeError("No se pudo cargar el modelo o los scalers")

    try:
        datos = pd.read_excel(ruta_entrada)
        log(f"✅ Datos de validación cargados: {datos.shape[0]} muestras")
    except Exception as e:
        raise RuntimeError(f"Error cargando datos: {e}") from e

    columnas_espectrales = [f'L{i}' for i in range(328, 1073)]
    columnas_faltantes = [col for col in columnas_espectrales if col not in datos.columns]
    if columnas_faltantes:
        faltantes_preview = ', '.join(columnas_faltantes[:5])
        raise RuntimeError(f"Columnas faltantes en el Excel: {faltantes_preview}...")

    X = datos[columnas_espectrales]
    log(f"✅ Datos espectrales preparados: {X.shape}")

    try:
        X_scaled = scaler_X.transform(X)
        log("✅ Datos escalados correctamente")
    except Exception as e:
        raise RuntimeError(f"Error escalando datos: {e}") from e

    try:
        log("🔄 Realizando predicciones...")
        predicciones_scaled = model.predict(X_scaled, verbose=1 if verbose else 0)
        log("✅ Predicciones realizadas")
    except Exception as e:
        raise RuntimeError(f"Error en predicción: {e}") from e

    try:
        predicciones = scaler_y.inverse_transform(predicciones_scaled)
        log("✅ Escalado revertido")
    except Exception as e:
        raise RuntimeError(f"Error revirtiendo escalado: {e}") from e

    resultados = pd.DataFrame(predicciones, columns=[
        'PH', 'CONDUCTIVIDAD', 'TDS', 'NITRATOS', 'FOSFATOS', 'DQO'
    ])

    for col in ['MUESTRA', 'ID', 'CODIGO']:
        if col in datos.columns:
            resultados[col] = datos[col].values

    resultados.to_excel(ruta_salida, index=False)
    log("\n🎯 PREDICCIONES FINALIZADAS EXITOSAMENTE")
    log("=" * 50)
    log("Primeras 5 predicciones:")
    log(str(resultados.head().round(4)))
    log("\n📊 Estadísticas de las predicciones:")
    log(str(resultados.describe().round(4)))
    log(f"\n💾 Resultados guardados en: '{ruta_salida}'")

    return resultados


def main():
    try:
        predecir_desde_excel('DATOS_VALIDACION.xlsx', 'predicciones_finales.xlsx', verbose=True)
    except Exception as e:
        print(f"❌ {e}")


if __name__ == "__main__":
    main()