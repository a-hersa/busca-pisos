from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import reactive
from shiny.express import render, input, ui
from shinywidgets import render_plotly
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

# Database configuration
DB_URI = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@inmobiliario-postgres:5432/inmobiliario_db'
engine = create_engine(DB_URI)

# Page configuration
ui.page_opts(
    title="Análisis Inmobiliario - Dashboard", 
    fillable=True,
    full_width=True
)

# Data fetching functions
@reactive.calc
def fetch_data():
    """Fetch all property data from database"""
    try:
        query = """
        SELECT p_id, nombre, fecha_new, fecha_updated, precio, metros, 
               habitaciones, planta, ascensor, poblacion, url, descripcion, estatus
        FROM propiedades 
        WHERE precio > 0 AND metros > 0
        ORDER BY fecha_updated DESC
        """
        data = pd.read_sql_query(query, engine)
        
        # Data processing
        data["fecha_updated"] = pd.to_datetime(data["fecha_updated"])
        data["precio_m2"] = data["precio"] / data["metros"]
        data["mes_año"] = data["fecha_updated"].dt.strftime('%Y-%m')
        
        return data
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return pd.DataFrame()

@reactive.calc
def get_locations():
    """Get unique locations from database"""
    df = fetch_data()
    if df.empty:
        return ["No data available"]
    
    locations = df[df["poblacion"] != "Ubicación no especificada"]["poblacion"].unique()
    locations = [loc for loc in locations if loc is not None and loc.strip() != ""]
    return sorted(locations) if len(locations) > 0 else ["No locations available"]

@reactive.calc
def get_filtered_data():
    """Get filtered data based on user selections"""
    df = fetch_data()
    if df.empty:
        return df
    
    # Filter by location
    if input.location() != "Todas":
        df = df[df["poblacion"] == input.location()]
    
    # Filter by price range
    price_range = input.price_range()
    df = df[(df["precio"] >= price_range[0]) & (df["precio"] <= price_range[1])]
    
    # Filter by size range
    size_range = input.size_range()
    df = df[(df["metros"] >= size_range[0]) & (df["metros"] <= size_range[1])]
    
    return df

# UI Layout
with ui.sidebar(width=300):
    ui.h3("Filtros de Análisis")
    
    # Location filter
    @render.ui
    def location_filter():
        locations = get_locations()
        choices = ["Todas"] + locations
        return ui.input_selectize(
            "location",
            "Selecciona una población:",
            choices=choices,
            selected="Todas"
        )
    
    # Price range filter
    @render.ui
    def price_range_filter():
        df = fetch_data()
        if df.empty:
            return ui.input_slider("price_range", "Rango de precios (€):", min=0, max=120000, value=[0, 120000])
        
        min_price = int(df["precio"].min())
        max_price = int(df["precio"].max())
        return ui.input_slider(
            "price_range", 
            "Rango de precios (€):", 
            min=min_price, 
            max=max_price, 
            value=[min_price, max_price],
            step=5000
        )
    
    # Size range filter
    @render.ui
    def size_range_filter():
        df = fetch_data()
        if df.empty:
            return ui.input_slider("size_range", "Rango de metros (m²):", min=0, max=200, value=[0, 200])
        
        min_size = int(df["metros"].min())
        max_size = int(df["metros"].max())
        return ui.input_slider(
            "size_range", 
            "Rango de metros (m²):", 
            min=min_size, 
            max=max_size, 
            value=[min_size, max_size],
            step=10
        )
    
    # Chart type selector
    ui.input_radio_buttons(
        "chart_type",
        "Tipo de gráfico:",
        choices={
            "line": "Evolución temporal",
            "scatter": "Precio vs Metros",
            "histogram": "Distribución precios",
            "box": "Comparación por ubicación"
        },
        selected="line"
    )

# Main content area
with ui.layout_columns(col_widths=[3, 3, 3, 3]):
    # KPI Cards
    with ui.value_box(theme="primary"):
        "Total Propiedades"
        @render.text
        def total_properties():
            df = get_filtered_data()
            return f"{len(df):,}"
    
    with ui.value_box(theme="success"):
        "Precio Promedio"
        @render.text
        def avg_price():
            df = get_filtered_data()
            if df.empty:
                return "€0"
            return f"€{df['precio'].mean():,.0f}"
    
    with ui.value_box(theme="info"):
        "Precio por m² Promedio"
        @render.text
        def avg_price_m2():
            df = get_filtered_data()
            if df.empty:
                return "€0/m²"
            return f"€{df['precio_m2'].mean():.0f}/m²"
    
    with ui.value_box(theme="warning"):
        "Metros Promedio"
        @render.text
        def avg_size():
            df = get_filtered_data()
            if df.empty:
                return "0 m²"
            return f"{df['metros'].mean():.0f} m²"

# Main visualization area
with ui.layout_columns(col_widths=[8, 4]):
    # Main chart
    with ui.card(full_screen=True):
        ui.card_header("Análisis de Propiedades")
        
        @render_plotly
        def main_chart():
            df = get_filtered_data()
            
            if df.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text="No hay datos disponibles con los filtros seleccionados",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )
                return fig
            
            chart_type = input.chart_type()
            
            if chart_type == "line":
                # Price evolution over time
                df_grouped = df.groupby(["mes_año", "poblacion"]).agg({
                    "precio_m2": "mean",
                    "precio": "mean"
                }).reset_index()
                
                fig = px.line(
                    df_grouped, 
                    x="mes_año", 
                    y="precio_m2",
                    color="poblacion",
                    title="Evolución del Precio por m² en el Tiempo",
                    labels={"precio_m2": "Precio por m² (€)", "mes_año": "Fecha"}
                )
                
            elif chart_type == "scatter":
                # Price vs Size scatter
                fig = px.scatter(
                    df, 
                    x="metros", 
                    y="precio",
                    color="poblacion",
                    size="precio_m2",
                    hover_data=["nombre", "habitaciones"],
                    title="Precio vs Metros Cuadrados",
                    labels={"metros": "Metros (m²)", "precio": "Precio (€)"}
                )
                
            elif chart_type == "histogram":
                # Price distribution
                fig = px.histogram(
                    df, 
                    x="precio",
                    color="poblacion",
                    nbins=20,
                    title="Distribución de Precios",
                    labels={"precio": "Precio (€)", "count": "Número de Propiedades"}
                )
                
            elif chart_type == "box":
                # Price comparison by location
                fig = px.box(
                    df, 
                    x="poblacion", 
                    y="precio_m2",
                    title="Comparación de Precios por m² por Ubicación",
                    labels={"poblacion": "Ubicación", "precio_m2": "Precio por m² (€)"}
                )
                fig.update_xaxis(tickangle=45)
            
            fig.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            return fig
    
    # Statistics panel
    with ui.card():
        ui.card_header("Estadísticas Detalladas")
        
        @render.ui
        def statistics_panel():
            df = get_filtered_data()
            
            if df.empty:
                return ui.p("No hay datos disponibles")
            
            stats = []
            
            # Price statistics
            stats.append(ui.h4("Precios"))
            stats.append(ui.p(f"Mínimo: €{df['precio'].min():,.0f}"))
            stats.append(ui.p(f"Máximo: €{df['precio'].max():,.0f}"))
            stats.append(ui.p(f"Mediana: €{df['precio'].median():,.0f}"))
            
            # Size statistics
            stats.append(ui.h4("Metros"))
            stats.append(ui.p(f"Mínimo: {df['metros'].min():.0f} m²"))
            stats.append(ui.p(f"Máximo: {df['metros'].max():.0f} m²"))
            stats.append(ui.p(f"Mediana: {df['metros'].median():.0f} m²"))
            
            # Price per m² statistics
            stats.append(ui.h4("Precio por m²"))
            stats.append(ui.p(f"Mínimo: €{df['precio_m2'].min():.0f}/m²"))
            stats.append(ui.p(f"Máximo: €{df['precio_m2'].max():.0f}/m²"))
            stats.append(ui.p(f"Mediana: €{df['precio_m2'].median():.0f}/m²"))
            
            # Location breakdown
            if len(df['poblacion'].unique()) > 1:
                stats.append(ui.h4("Por Ubicación"))
                location_stats = df.groupby('poblacion').agg({
                    'precio': 'mean',
                    'precio_m2': 'mean'
                }).round(0)
                
                for location, data in location_stats.iterrows():
                    stats.append(ui.p(f"{location}: €{data['precio']:,.0f} (€{data['precio_m2']:.0f}/m²)"))
            
            return ui.div(*stats)

# Data table
with ui.card():
    ui.card_header("Tabla de Propiedades")
    
    @render.data_frame
    def properties_table():
        df = get_filtered_data()
        
        if df.empty:
            return pd.DataFrame({"Mensaje": ["No hay datos disponibles con los filtros seleccionados"]})
        
        # Select and format columns for display
        display_df = df[['nombre', 'poblacion', 'precio', 'metros', 'precio_m2', 'habitaciones', 'fecha_updated']].copy()
        display_df['precio'] = display_df['precio'].apply(lambda x: f"€{x:,.0f}")
        display_df['precio_m2'] = display_df['precio_m2'].apply(lambda x: f"€{x:.0f}/m²")
        display_df['metros'] = display_df['metros'].apply(lambda x: f"{x:.0f} m²")
        display_df['fecha_updated'] = display_df['fecha_updated'].dt.strftime('%Y-%m-%d')
        
        # Rename columns for better display
        display_df.columns = ['Nombre', 'Ubicación', 'Precio', 'Metros', 'Precio/m²', 'Habitaciones', 'Actualizado']
        
        return display_df