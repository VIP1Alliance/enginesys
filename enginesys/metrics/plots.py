import numpy as np
import pandas as pd
import plotly.graph_objects as go


def plot_hist_index(log_variation, strategy, metrics_df, num_bins=10):
    
    metric_values = metrics_df.loc[strategy]
    
    # Create the histogram to get the bins automatically
    
    
    hist, bin_edges = np.histogram(log_variation[strategy].dropna(), bins=num_bins)
    
    # Define the colors for the histogram bars
    colors = ["#4479EA"] * num_bins
    reference_colors = ["#EA4444", "#EAA644"]
    anotations = []

    for j, metric in enumerate(metric_values.index):
        
        value = metric_values[metric]
        
        # If the metric value is finite, information is generated for the annotation
        if np.isfinite(value):
            if value < bin_edges[0]:
                # If the value is less than the smallest bin, place it at the far left
                x_pos = bin_edges[0]
                y_pos = 0
                text = f"{metric}: {value:.2%}"
            elif value >= bin_edges[-1]:
                # If the value is greater than the largest bin, place it at the far right
                x_pos = bin_edges[-1]
                y_pos = 0
                text = f"{metric}: {value:.2%}"
            else:
                # If the value is within the bins, find the corresponding bin
                for i in range(num_bins):
                    if bin_edges[i] <= value < bin_edges[i + 1]:
                        colors[i] = reference_colors[j]
                        x_pos = (bin_edges[i] + bin_edges[i + 1]) / 2
                        y_pos = hist[i]
                        text = f"{metric} <br> {value:.2%}"
                        break
            
            # Agregar diccionario con la información de la anotación a la lista 'anotaciones'
            anotations.append(
                {
                    "x": x_pos,
                    "y": y_pos,
                    "text": text,
                    "ax": 0,
                    "ay": -90,
                    "showarrow": False,
                    "yshift":30,
                    "font": {
                        "color": reference_colors[j],
                        # 'family': 'Arial, sans-serif',  # Puedes cambiar la fuente si lo deseas
                        "size": 16,  # Tamaño de la fuente
                        "weight": "bold",  # Negrita
                    },
                }
            )

    # Create the histogram bars with the calculated values and colors
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

    # Create the figure with the histogram bars
    fig = go.Figure(data=bar_data)

    # Add the annotations to the figure
    for anotacion in anotations:
        fig.add_annotation(anotacion)
    
    # Define the title of the figure
    text_title=(
        f"<b>Comportamiento de la Estrategia <br> {strategy} (Valor en riesgo VaR)</b>"
        if strategy != "Algoritmo GEA"
        else "<b>Comportamiento del Algoritmo GEA <br> (Valor en riesgo VaR)</b>"
    )

    # Update the layout of the figure
    fig.update_layout(
        title={
            'text': text_title.upper(),  # Title of the figure with uppercase letters
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(               # Font of the title
                family="Arial",
                size=24,
                color="#002060"
            ),
        },
        template="plotly_white",
        height=500,
        width=800,
        bargap=0.1,  # This value modifies the width of the bars
        showlegend=False,  # Hide the legend
        xaxis=dict(
            tickformat=".1%",  # Format of the x-axis ticks as percentages with one decimal
        ),
        paper_bgcolor='rgba(0,0,0,0)',  # Background color of the paper
        plot_bgcolor='rgba(0,0,0,0)',   # Background color of the plot
    )

    return fig

def plot_risk_metrics(log_variation_df: pd.DataFrame, risk_metrics_df: pd.DataFrame):
    behavior_histograms = {}
    for strategy in log_variation_df.columns:
        strategy_plot = plot_hist_index(log_variation_df, strategy, risk_metrics_df)
        behavior_histograms[strategy] = strategy_plot
    return behavior_histograms