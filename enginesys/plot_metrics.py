import plotly.graph_objects as go
import numpy as np


def plot_hist_index(log_variation, strategy, individual_metrics_df, num_bins=10):
    
    metrics_values = individual_metrics_df.loc[strategy]
    
    # Crear el histograma para obtener los bins automáticamente
    hist, bin_edges = np.histogram(log_variation[strategy], bins=num_bins)
    
    # Identificar el bin que contiene el valor específico
    colors = ["#4479EA"] * num_bins
    colores_referencia = ["#EA4444", "#EAA644"]
    anotaciones = []

    # for j, metric in enumerate(metrics_values.keys()):
    for j, metric in enumerate(metrics_values.index):
        
        value = metrics_values[metric]
        
        # Si el valor de la métrica es finito se genera información para la anotación
        if np.isfinite(value):
            if value < bin_edges[0]:
                # Si el valor es menor que el menor bin, colocarlo en la posición más a la izquierda
                x_pos = bin_edges[0]
                y_pos = 0
                text = f"{metric}: {value:.2%}"
            elif value >= bin_edges[-1]:
                # Si el valor es mayor o igual al mayor bin, colocarlo en la posición más a la derecha
                x_pos = bin_edges[-1]
                y_pos = 0
                text = f"{metric}: {value:.2%}"
            else:
                # Valor dentro del rango de bins
                for i in range(num_bins):
                    if bin_edges[i] <= value < bin_edges[i + 1]:
                        colors[i] = colores_referencia[j]
                        x_pos = (bin_edges[i] + bin_edges[i + 1]) / 2
                        y_pos = hist[i]
                        text = f"{metric} <br> {value:.2%}"
                        break
            
            # Agregar diccionario con la información de la anotación a la lista 'anotaciones'
            anotaciones.append(
                {
                    "x": x_pos,
                    "y": y_pos,
                    "text": text,
                    "ax": 0,
                    "ay": -90,
                    "showarrow": False,
                    "yshift":30,
                    "font": {
                        "color": colores_referencia[j],
                        # 'family': 'Arial, sans-serif',  # Puedes cambiar la fuente si lo deseas
                        "size": 16,  # Tamaño de la fuente
                        "weight": "bold",  # Negrita
                    },
                }
            )

    # Crear datos para el histograma con colores personalizados
    bar_data = []
    for i in range(num_bins):
        bar_data.append(
            go.Bar(
                x=[(bin_edges[i] + bin_edges[i + 1]) / 2],  # centro del bin
                y=[hist[i]],
                marker_color=colors[i],
                width=bin_edges[i + 1] - bin_edges[i],
                showlegend=True,  # Desactivar la leyenda
            )
        )

    # Crear la figura con los datos del histograma
    fig = go.Figure(data=bar_data)

    # Agregar anotaciones
    for anotacion in anotaciones:
        fig.add_annotation(anotacion)
    
    text_title=(
        f"<b>Comportamiento de la Estrategia <br> {strategy} (Valor en riesgo VaR)</b>"
        if strategy != "Algoritmo GEA"
        else "<b>Comportamiento del Algoritmo GEA <br> (Valor en riesgo VaR)</b>"
    )

    # Personalizar detalles de diseño de la figura (título, ejes, plantilla, tamaño, etc.)
    fig.update_layout(
        title={
            'text': text_title.upper(),  # Convertir a mayúsculas
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family="Arial",
                size=24,
                color="#002060"
            ),
        },
        # yaxis_title="",
        template="plotly_white",
        height=500,
        width=800,
        # title_x=0.5,
        bargap=0.1,  # Aumenta este valor para reducir el ancho de las barras
        showlegend=False,  # Desactivar la leyenda
        xaxis=dict(
            tickformat=".1%",  # Formato de porcentaje con dos decimales
        ),
        paper_bgcolor='rgba(0,0,0,0)',  # Fondo transparente para la figura completa
        plot_bgcolor='rgba(0,0,0,0)',   # Fondo transparente para el área de trazado
    )

    return fig