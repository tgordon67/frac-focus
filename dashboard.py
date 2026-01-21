"""
Interactive Dashboard for FracFocus Proppant & Water Analysis

This dashboard provides interactive visualizations for exploring proppant
and water consumption trends by quarter and region.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from typing import Optional, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path('output')
DATA_FILES = {
    'basin': OUTPUT_DIR / 'quarterly_by_basin.csv',
    'state': OUTPUT_DIR / 'quarterly_by_state.csv',
    'county': OUTPUT_DIR / 'quarterly_by_county.csv',
    'permian_county': OUTPUT_DIR / 'permian_by_county.csv',
    'detail': OUTPUT_DIR / 'quarterly_detail.csv'
}


class FracFocusDashboard:
    """Interactive dashboard for FracFocus analysis"""

    def __init__(self):
        self.data = {}
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.load_data()
        self.setup_layout()
        self.setup_callbacks()

    def load_data(self):
        """Load all analysis output files"""
        logger.info("Loading data files...")

        for key, filepath in DATA_FILES.items():
            if filepath.exists():
                self.data[key] = pd.read_csv(filepath)
                logger.info(f"Loaded {key}: {len(self.data[key]):,} rows")
            else:
                logger.warning(f"File not found: {filepath}")

        if not self.data:
            raise FileNotFoundError(
                "No data files found. Please run fracfocus_analysis.py first."
            )

    def create_time_series_plot(self, df: pd.DataFrame, metric: str,
                               title: str, region_col: Optional[str] = None,
                               regions: Optional[List[str]] = None) -> go.Figure:
        """
        Create interactive time series plot.

        Args:
            df: DataFrame with Quarter and metric columns
            metric: Column to plot (Proppant_MM_lbs, Water_MM_gal, Well_count)
            title: Plot title
            region_col: Column to use for grouping (Basin, StateName, etc.)
            regions: List of specific regions to plot

        Returns:
            Plotly figure
        """
        # Filter data if regions specified
        if region_col and regions:
            df = df[df[region_col].isin(regions)]

        # Determine y-axis label
        y_labels = {
            'Proppant_MM_lbs': 'Proppant (Million lbs)',
            'Water_MM_gal': 'Water (Million gallons)',
            'Well_count': 'Number of Wells',
            'Avg_Proppant_per_Well_lbs': 'Avg Proppant per Well (lbs)',
            'Avg_Water_per_Well_gal': 'Avg Water per Well (gallons)'
        }
        y_label = y_labels.get(metric, metric)

        fig = go.Figure()

        if region_col:
            # Multi-line plot (one line per region)
            for region in df[region_col].unique():
                region_data = df[df[region_col] == region].sort_values('Quarter')

                fig.add_trace(go.Scatter(
                    x=region_data['Quarter'],
                    y=region_data[metric],
                    mode='lines+markers',
                    name=region,
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  'Quarter: %{x}<br>' +
                                  f'{y_label}: %{{y:,.1f}}<br>' +
                                  '<extra></extra>'
                ))
        else:
            # Single line plot
            df_sorted = df.sort_values('Quarter')

            fig.add_trace(go.Scatter(
                x=df_sorted['Quarter'],
                y=df_sorted[metric],
                mode='lines+markers',
                name=metric,
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8),
                hovertemplate='Quarter: %{x}<br>' +
                              f'{y_label}: %{{y:,.1f}}<br>' +
                              '<extra></extra>'
            ))

        fig.update_layout(
            title=title,
            xaxis_title='Quarter',
            yaxis_title=y_label,
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )

        return fig

    def create_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                        title: str, top_n: int = 10) -> go.Figure:
        """
        Create horizontal bar chart for top N regions.

        Args:
            df: DataFrame
            x_col: Column for x-axis (metric)
            y_col: Column for y-axis (region name)
            title: Plot title
            top_n: Number of top regions to show

        Returns:
            Plotly figure
        """
        # Aggregate and get top N
        df_agg = df.groupby(y_col)[x_col].sum().reset_index()
        df_top = df_agg.nlargest(top_n, x_col).sort_values(x_col)

        fig = go.Figure(go.Bar(
            x=df_top[x_col],
            y=df_top[y_col],
            orientation='h',
            marker=dict(color='#2ca02c'),
            hovertemplate='<b>%{y}</b><br>' +
                          f'{x_col}: %{{x:,.0f}}<br>' +
                          '<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            xaxis_title=x_col,
            yaxis_title='',
            template='plotly_white',
            height=400
        )

        return fig

    def setup_layout(self):
        """Setup dashboard layout"""

        # Get available regions for dropdowns
        basins = sorted(self.data['basin']['Basin'].unique()) if 'basin' in self.data else []
        states = sorted(self.data['state']['StateName'].unique()) if 'state' in self.data else []

        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("FracFocus Proppant & Water Analysis Dashboard",
                           className="text-center mb-4 mt-4"),
                    html.Hr()
                ])
            ]),

            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Controls", className="card-title"),

                            html.Label("View Level:", className="mt-3"),
                            dcc.Dropdown(
                                id='view-level',
                                options=[
                                    {'label': 'Basin View', 'value': 'basin'},
                                    {'label': 'State View', 'value': 'state'},
                                    {'label': 'Permian Basin (County)', 'value': 'permian_county'}
                                ],
                                value='basin',
                                clearable=False
                            ),

                            html.Label("Metric:", className="mt-3"),
                            dcc.Dropdown(
                                id='metric',
                                options=[
                                    {'label': 'Proppant (Million lbs)', 'value': 'Proppant_MM_lbs'},
                                    {'label': 'Water (Million gallons)', 'value': 'Water_MM_gal'},
                                    {'label': 'Well Count', 'value': 'Well_count'},
                                    {'label': 'Avg Proppant per Well', 'value': 'Avg_Proppant_per_Well_lbs'},
                                    {'label': 'Avg Water per Well', 'value': 'Avg_Water_per_Well_gal'}
                                ],
                                value='Proppant_MM_lbs',
                                clearable=False
                            ),

                            html.Label("Select Regions (Basin View):", className="mt-3"),
                            dcc.Dropdown(
                                id='basin-selector',
                                options=[{'label': b, 'value': b} for b in basins],
                                value=basins[:5] if len(basins) >= 5 else basins,
                                multi=True
                            ),

                            html.Label("Select States (State View):", className="mt-3"),
                            dcc.Dropdown(
                                id='state-selector',
                                options=[{'label': s, 'value': s} for s in states],
                                value=states[:5] if len(states) >= 5 else states,
                                multi=True
                            ),

                            html.Div([
                                dbc.Button("Download Data", id="download-btn",
                                          color="primary", className="mt-4 w-100"),
                                dcc.Download(id="download-data")
                            ])
                        ])
                    ])
                ], width=3),

                # Main visualization area
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Time Series Analysis", className="card-title"),
                            dcc.Loading(
                                id="loading-time-series",
                                type="default",
                                children=dcc.Graph(id='time-series-plot')
                            )
                        ])
                    ], className="mb-3"),

                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Top Regions (Total)", className="card-title"),
                            dcc.Loading(
                                id="loading-bar-chart",
                                type="default",
                                children=dcc.Graph(id='bar-chart')
                            )
                        ])
                    ])
                ], width=9)
            ]),

            # Summary Statistics
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Summary Statistics", className="card-title"),
                            html.Div(id='summary-stats')
                        ])
                    ])
                ])
            ], className="mt-3 mb-5")

        ], fluid=True)

    def setup_callbacks(self):
        """Setup interactive callbacks"""

        @self.app.callback(
            [Output('time-series-plot', 'figure'),
             Output('bar-chart', 'figure'),
             Output('summary-stats', 'children')],
            [Input('view-level', 'value'),
             Input('metric', 'value'),
             Input('basin-selector', 'value'),
             Input('state-selector', 'value')]
        )
        def update_plots(view_level, metric, selected_basins, selected_states):
            """Update plots based on selections"""

            # Determine which data to use
            if view_level == 'basin':
                df = self.data['basin'].copy()
                region_col = 'Basin'
                regions = selected_basins if selected_basins else df['Basin'].unique()
                title_prefix = "Basin"
            elif view_level == 'state':
                df = self.data['state'].copy()
                region_col = 'StateName'
                regions = selected_states if selected_states else df['StateName'].unique()
                title_prefix = "State"
            elif view_level == 'permian_county':
                if 'permian_county' not in self.data:
                    # Return empty figures if no Permian data
                    empty_fig = go.Figure()
                    empty_fig.add_annotation(text="No Permian Basin data available",
                                            showarrow=False)
                    return empty_fig, empty_fig, html.Div("No data available")

                df = self.data['permian_county'].copy()
                region_col = 'CountyName'
                regions = None  # Show all counties
                title_prefix = "Permian Basin County"
            else:
                df = self.data['basin'].copy()
                region_col = 'Basin'
                regions = selected_basins
                title_prefix = "Basin"

            # Create time series plot
            time_series_fig = self.create_time_series_plot(
                df, metric,
                title=f"{title_prefix} {metric} by Quarter",
                region_col=region_col,
                regions=regions
            )

            # Create bar chart
            bar_chart_fig = self.create_bar_chart(
                df, metric, region_col,
                title=f"Top 10 {title_prefix}s by {metric}",
                top_n=10
            )

            # Calculate summary statistics
            if regions and region_col:
                df_filtered = df[df[region_col].isin(regions)]
            else:
                df_filtered = df

            total_proppant = df_filtered['Proppant_lbs'].sum() / 1e9 if 'Proppant_lbs' in df_filtered.columns else 0
            total_water = df_filtered['Water_gal'].sum() / 1e9 if 'Water_gal' in df_filtered.columns else 0
            total_wells = df_filtered['Well_count'].sum() if 'Well_count' in df_filtered.columns else 0
            num_quarters = df_filtered['Quarter'].nunique()

            summary = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H5(f"{total_proppant:.2f} Billion lbs"),
                        html.P("Total Proppant", className="text-muted")
                    ], width=3),
                    dbc.Col([
                        html.H5(f"{total_water:.2f} Billion gal"),
                        html.P("Total Water", className="text-muted")
                    ], width=3),
                    dbc.Col([
                        html.H5(f"{total_wells:,}"),
                        html.P("Total Wells", className="text-muted")
                    ], width=3),
                    dbc.Col([
                        html.H5(f"{num_quarters}"),
                        html.P("Quarters", className="text-muted")
                    ], width=3)
                ])
            ])

            return time_series_fig, bar_chart_fig, summary

        @self.app.callback(
            Output("download-data", "data"),
            Input("download-btn", "n_clicks"),
            [State('view-level', 'value'),
             State('basin-selector', 'value'),
             State('state-selector', 'value')],
            prevent_initial_call=True
        )
        def download_data(n_clicks, view_level, selected_basins, selected_states):
            """Download filtered data as CSV"""

            if view_level == 'basin':
                df = self.data['basin'].copy()
                if selected_basins:
                    df = df[df['Basin'].isin(selected_basins)]
            elif view_level == 'state':
                df = self.data['state'].copy()
                if selected_states:
                    df = df[df['StateName'].isin(selected_states)]
            elif view_level == 'permian_county':
                df = self.data['permian_county'].copy()
            else:
                df = self.data['basin'].copy()

            return dcc.send_data_frame(df.to_csv, f"fracfocus_{view_level}_data.csv", index=False)

    def run(self, host='127.0.0.1', port=8050, debug=True):
        """Run the dashboard"""
        logger.info(f"Starting dashboard at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main execution function"""
    try:
        dashboard = FracFocusDashboard()
        dashboard.run(host='0.0.0.0')
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Please run 'python fracfocus_analysis.py' first to generate data files.")
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        raise


if __name__ == '__main__':
    main()
