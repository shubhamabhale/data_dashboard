import os
import dash
from dash import dcc, html
import pandas as pd
import psycopg2
import plotly.graph_objs as go
from dash import dash_table
import plotly.express as px
from datetime import datetime, timedelta
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


# Define database connection parameters
DB_HOST = "postgres"
DB_PORT = 5432
DB_NAME = "brx1"
DB_USER = "process_trending"
DB_PASSWORD = "abc123"

# Define table names
TABLE_NAMES = ["CM_HAM_DO_AI1/Temp_value", "CM_HAM_PH_AI1/pH_value", "CM_PID_DO/Process_DO", "CM_PRESSURE/Output"]

# Define styles
styles = {
    'title': {
        'textAlign': 'center',
        'color': '#7FDBFF',
        'margin': '2%'
    },
    'graph': {
        'display': 'flex',
        'flexWrap': 'wrap',
        'justifyContent': 'center'
    },
    'rangeSlider': {
        'margin': '2% 15% 2% 15%'
    },
    'background': {
        'backgroundColor': '#1E1E1E',
        'justifyContent':'space-around'
    },
    'normal': {
        'textAlign': 'center',
        'color': '#7FDBFF',
        'margin': '2%',
        'fontSize': 'px'
    },
    'subtitle': {
        'textAlign': 'center',
        'color': 'red',
        'margin': '2%',
        'fontSize': '18px'
    }
}


def connect_to_database():
    """Connect to the PostgreSQL database"""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn

def fetch_data(table_name, conn):
    """Fetch data from the specified table"""
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM \"{table_name}\";")
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        df = pd.DataFrame(data, columns=columns)
        return df

def fetch_all_data(table_names):
    """Fetch data from all specified tables"""
    with connect_to_database() as conn:
        data = {}
        for table_name in table_names:
            data[table_name] = fetch_data(table_name, conn)
        return data

def create_graph(table_name, data):
    """Create a graph with the specified table data"""
    fig = px.line(data, x="time", y="value")
    fig.update_layout(
        title=table_name,
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#1E1E1E',
        font={'color': '#7FDBFF'},
        xaxis={'title': 'Time', 'titlefont': {'color': '#7FDBFF'}, 'tickfont': {'color': '#7FDBFF'}},
        yaxis={'title': 'Value', 'titlefont': {'color': '#7FDBFF'}, 'tickfont': {'color': '#7FDBFF'}},
        height=600,
        width=1300
    )
    return dcc.Graph(figure=fig, id=f'graph-{table_name}', )

def create_graphs(table_names, data):
    """Create a graph for each table data"""
    return [create_graph(table_name, data[table_name]) for table_name in table_names]

def create_dashboard():
    """Create the Plotly Dash app dashboard"""
    
    app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'], suppress_callback_exceptions=True)
    data = fetch_all_data(TABLE_NAMES)
    graphs = create_graphs(TABLE_NAMES, data)
    temperature_graph = graphs[0] # Get the graph corresponding to temperature
    graphs.remove(temperature_graph) # Remove the temperature graph from the list of graphs
    graphs.insert(0, temperature_graph) # Insert the temperature graph at the beginning of the list of graphs
        
    app.layout = html.Div(
    style=styles['background'],
    children=[
        html.Div(
            style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'margin': '2%',
            },
            children=[
                html.H1(
                    children='BRX1 Dashboard- Shubham Abhale',
                    style=styles['title']
                ),
                html.Button(
                    'Get / Refresh Data',
                    id='refresh-data-btn',
                    n_clicks=0,
                    style={
                        'backgroundColor': 'white',
                        'marginLeft': 'auto',
                    },
                ),
                dcc.Interval(
                    id='refresh-data-interval',
                    interval=1500,
                    n_intervals=0,
                ),
            ],
        ),
        html.H2(
            children='Select required option or hit Refresh Data',
            style=styles['subtitle'],
        ),
        
        html.H3(
            children='Select the area to zoom for the specific time',
            style=styles['normal'],
        ),
        html.Div(
            style={
                'width': '30%',
                'margin': 'auto',
            },
            children=[
                dcc.Dropdown(
                    id='parameter-dropdown',
                    options=[
                        {'label': 'Temperature', 'value': 'CM_HAM_DO_AI1/Temp_value'},
                        {'label': 'pH', 'value': 'CM_HAM_PH_AI1/pH_value'},
                        {'label': 'Distilled Oxygen', 'value': 'CM_PID_DO/Process_DO'},
                        {'label': 'Pressure', 'value': 'CM_PRESSURE/Output'},
                    ],
                    value='CM_HAM_DO_AI1/Temp_value',
                    clearable=False,
                    style={'width': '100%'},
                ),
            ],
        ),
        html.Div(
            id='graphs-container',
            style=styles['graph'],
            children=[],
        ),
        html.Div(
            style={'textAlign': 'center'},
            children=[
                html.Button(
                    'Download as csv',
                    id='download-button',
                    style={'backgroundColor': 'green'},
                    n_clicks=0,
                ),
                dcc.Download(id='download-dataframe-csv'),
            ],
        ),
    ],
)

    
    
    @app.callback(
        Output('graphs-container', 'children'),
        [Input('parameter-dropdown', 'value'), Input('refresh-data-btn', 'n_clicks'), Input('refresh-data-interval', 'n_intervals')],
        [State('parameter-dropdown', 'value')]
    )
    def display_graph(parameter, n_clicks, n_intervals, current_parameter):
        ctx = dash.callback_context
        if ctx.triggered[0]['prop_id'] == 'parameter-dropdown.value':
            table_name = parameter.split('/')[-1]
            data = fetch_data(parameter, connect_to_database())
            graph = create_graph(table_name, data)
            return [graph]
        elif ctx.triggered[0]['prop_id'] == 'refresh-data-btn.n_clicks':
            table_name = current_parameter.split('/')[-1]
            data = fetch_data(current_parameter, connect_to_database())
            graph = create_graph(table_name, data)
            return [graph]
        else:
            raise PreventUpdate
        
    @app.callback(
        Output('download-dataframe-csv', 'data'),
        Input('download-button', 'n_clicks'),
        State('parameter-dropdown', 'value')
    )
    def download_data(n_clicks, parameter):
        if n_clicks == 0:
            raise PreventUpdate
        data = fetch_data(parameter, connect_to_database())
        csv_string = data.to_csv(index=False, encoding='utf-8-sig')
        return dict(content=csv_string, filename=f"{parameter.replace('/', '_')}_data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
    
    return app


if __name__ == '__main__':
    app = create_dashboard()
    app.run_server(host='0.0.0.0', port=8888, debug=True)