#######################
# Agente Basico De IA #
# Herramientas v2     #
# (FRED + Frankfurter)#
#######################

# Importacion para el manejo de sistema
import os
import csv
import requests

class IntermediateTools:

    def __init__(self):
        pass

    # Herramienta para consultar el tipo de cambio (se mantiene igual que en la version original)
    def consultar_tipo_cambio_api(self, moneda: str):
        print(f"Herramienta consultar_tipo_cambio_api llamada con moneda: {moneda}")

        if not moneda:
            return "Error: Se requiere el código de la moneda para obtener el tipo de cambio."

        url = f"https://open.er-api.com/v6/latest/{moneda.upper()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al consultar_tipo_cambio_api: {moneda}. Error: {e}")
            return f"ERROR: No se pudo obtener el tipo de cambio para la moneda: {moneda}"

    # Herramienta para consultar series economicas de la Reserva Federal (FRED)
    def consultar_serie_fred_api(self, serie_id: str, fecha_inicio: str, fecha_fin: str):
        print(f"Herramienta consultar_serie_fred_api llamada: serie={serie_id}, {fecha_inicio} a {fecha_fin}")

        if not serie_id:
            return "Error: Se requiere el código de la serie de FRED, por ejemplo FEDFUNDS."

        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={serie_id.upper()}&cosd={fecha_inicio}&coed={fecha_fin}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # La respuesta viene en formato CSV, no JSON. La parseamos manualmente.
            lineas = response.text.strip().splitlines()

            if len(lineas) < 2:
                return f"ERROR: No hay datos para la serie {serie_id} en ese rango de fechas."

            lector = csv.DictReader(lineas)
            columna_valor = lector.fieldnames[1]  # segunda columna: el nombre de la serie

            serie = []
            for fila in lector:
                valor_texto = fila[columna_valor].strip() if fila[columna_valor] else ""
                # FRED marca los datos faltantes con un punto "." o con una cadena vacia
                if valor_texto in ("", "."):
                    continue
                try:
                    valor_numerico = float(valor_texto)
                except ValueError:
                    continue
                serie.append({
                    "fecha": fila["observation_date"],
                    "valor": valor_numerico
                })

            if not serie:
                return f"ERROR: La serie {serie_id} no tiene datos numéricos válidos en ese rango."

            # Si la serie es muy larga (ej. datos diarios de varios meses), la resampleamos
            # a un valor por mes para no exceder el limite de tokens del modelo. Nos quedamos
            # con la ULTIMA observacion disponible de cada mes (cierre de mes).
            LIMITE_OBSERVACIONES = 60
            if len(serie) > LIMITE_OBSERVACIONES:
                por_mes = {}
                for punto in serie:
                    clave_mes = punto["fecha"][:7]  # "YYYY-MM"
                    por_mes[clave_mes] = punto  # se queda con la ultima observacion de ese mes

                serie_resampleada = list(por_mes.values())
                return {
                    "serie": serie_resampleada,
                    "nota": (
                        f"La serie original tenía {len(serie)} observaciones (frecuencia alta). "
                        f"Se resampleó a {len(serie_resampleada)} observaciones mensuales "
                        "(última disponible de cada mes) para optimizar la consulta."
                    )
                }

            return serie
        except Exception as e:
            print(f"Error al consultar_serie_fred_api: {e}")
            return f"ERROR: No se pudo obtener la serie {serie_id} de FRED"

    # Herramienta para consultar tipo de cambio historico entre 2 monedas (Frankfurter/BCE)
    def consultar_tipo_cambio_historico_api(self, moneda_origen: str, moneda_destino: str, fecha: str = "latest"):
        print(f"Herramienta consultar_tipo_cambio_historico_api llamada: {moneda_origen} -> {moneda_destino}, fecha: {fecha}")

        if not moneda_origen or not moneda_destino:
            return "Error: Se requiere moneda de origen y moneda de destino."

        url = f"https://api.frankfurter.app/{fecha}?from={moneda_origen.upper()}&to={moneda_destino.upper()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "rates" not in data or moneda_destino.upper() not in data["rates"]:
                return (
                    f"ERROR: No hay tipo de cambio disponible para {moneda_origen} -> {moneda_destino}. "
                    f"Frankfurter solo soporta monedas de referencia del BCE (no incluye GTQ, por ejemplo)."
                )

            return data
        except Exception as e:
            print(f"Error al consultar_tipo_cambio_historico_api: {e}")
            return f"ERROR: No se pudo obtener el tipo de cambio entre {moneda_origen} y {moneda_destino}"

    # Herramienta para calcular variacion entre periodos consecutivos de una serie
    def calcular_variacion_porcentual(self, valores: list, etiquetas: list = None, es_tasa: bool = False):
        print(f"Herramienta calcular_variacion_porcentual llamada con {len(valores) if valores else 0} valores, es_tasa={es_tasa}")

        if not valores or len(valores) < 2:
            return "Error: Se necesitan al menos 2 valores para calcular variación."

        if not etiquetas:
            etiquetas = [f"periodo_{i}" for i in range(len(valores))]

        variaciones = []
        for i in range(1, len(valores)):
            anterior = valores[i - 1]
            actual = valores[i]

            if es_tasa:
                diferencia_pp = actual - anterior
                variaciones.append({
                    "desde": etiquetas[i - 1],
                    "hasta": etiquetas[i],
                    "variacion_puntos_porcentuales": round(diferencia_pp, 2)
                })
            else:
                if anterior == 0:
                    variaciones.append({
                        "desde": etiquetas[i - 1],
                        "hasta": etiquetas[i],
                        "variacion_pct": None
                    })
                    continue

                variacion_pct = ((actual - anterior) / abs(anterior)) * 100
                variaciones.append({
                    "desde": etiquetas[i - 1],
                    "hasta": etiquetas[i],
                    "variacion_pct": round(variacion_pct, 2)
                })

        return variaciones

    # Herramienta para calcular estadisticas descriptivas de una serie
    def calcular_estadisticas_descriptivas(self, valores: list):
        print(f"Herramienta calcular_estadisticas_descriptivas llamada con {len(valores) if valores else 0} valores")

        if not valores or len(valores) < 2:
            return "Error: Se necesitan al menos 2 valores para calcular estadísticas."

        n = len(valores)
        media = sum(valores) / n
        varianza = sum((x - media) ** 2 for x in valores) / n
        desviacion_estandar = varianza ** 0.5

        resultado = {
            "n_observaciones": n,
            "media": round(media, 4),
            "desviacion_estandar": round(desviacion_estandar, 4),
            "minimo": round(min(valores), 4),
            "maximo": round(max(valores), 4)
        }

        CV_LIMITE_INTERPRETABLE = 300

        if media == 0:
            resultado["coeficiente_variacion_pct"] = None
            resultado["nota_cv"] = "El coeficiente de variación no se reporta porque la media es cero."
        else:
            cv = (desviacion_estandar / media) * 100
            if abs(cv) > CV_LIMITE_INTERPRETABLE:
                resultado["coeficiente_variacion_pct"] = None
                resultado["nota_cv"] = (
                    f"El coeficiente de variación calculado ({round(cv, 1)}%) supera el límite "
                    f"interpretable ({CV_LIMITE_INTERPRETABLE}%), lo que indica que la media está "
                    "demasiado cerca de cero. Se recomienda interpretar solo la desviación estándar."
                )
            else:
                resultado["coeficiente_variacion_pct"] = round(cv, 2)

        return resultado