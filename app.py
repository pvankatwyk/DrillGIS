import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from datetime import datetime

settings = {
    # For dark mode...
    # 'background': '#1f2630',
    # 'background-2': '#252e3f',
    # 'text': '#7fafdf',
    # 'accent': '#2cfec1',

    'background': '#aad3df',
    'background-2': '#daecf1',
    'text': '#1f2630',
    'accent': '#008f05',

    'map_zoom': 3.25,
    'font-family': 'Open Sans, sans-serif'
}

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
server = app.server


def load_data(fp):
    df = pd.read_csv(fp)
    return df


# --- Functions to build graphics ---
def build_map(data, empty=False):
    # Tokens for custom maps ---
    # acccess_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"
    # mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
    # token = "pk.eyJ1IjoicHZhbmthdHd5ayIsImEiOiJja29hbmF3bTMwMnNxMnVsaHEya3J1bjBmIn0.-_ESAo1-Qogpzv66fVrh5Q"

    opacity = 0 if empty else 1
    map = px.scatter_mapbox(data,
                            lat=data.lat, lon=data.lon,
                            hover_name="job_type",
                            hover_data=["date", "machine_model", "drill_type", 'bit_diam', "usda_class",
                                        "mod_class",
                                        "weather", "avg_rop", "bore_fluid", "drill_depth"],
                            zoom=settings['map_zoom'],
                            color_discrete_sequence=[settings['accent']],
                            opacity=opacity
                            )
    map.update_layout(
        # Settings for custom maps --
        # mapbox_accesstoken=acccess_token,
        # mapbox_style=mapbox_style,

        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        plot_bgcolor=settings['background'],
        paper_bgcolor=settings['background'],
        font_color=settings['text'],
    )

    return map


def build_histogram(data, num_bins=10, empty=False):
    opacity = 0 if empty else 1
    hist = px.histogram(data,
                        x='avg_rop',
                        nbins=num_bins,
                        color_discrete_sequence=[settings['accent']],
                        opacity=opacity
                        )
    hist.update_layout(
        bargap=0.025,
        xaxis_title_text='Average ROP (ft/min)',
        yaxis_title_text='Count',
        margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor=settings['background-2']
    )
    hist.update_xaxes(
        range=[0, 5.5],
        color=settings['accent']
    )

    hist.update_yaxes(
        color=settings['accent']
    )

    return hist


def build_parameter_graph(parameter):
    if parameter is None:
        parameter = 'mod_class'
        label = 'Soil Type'
    else:
        label = parameter.title().replace('_', ' ')

    # If the parameter is categorical, use boxplot
    if parameter in ('job_type', 'machine_model', 'drill_type', 'bit_diam', 'bore_fluid', 'mod_class'):
        plt = px.box(geodf, x=parameter, y='avg_rop', color_discrete_sequence=[settings['accent']])
        plt.update_layout(
            xaxis_title_text=label,
            yaxis_title_text='Average ROP (ft/min)',
            margin=dict(l=0, r=0, t=5, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor=settings['background-2']
        )
    else:
        # Else (the parameter is continuous), use scatterplot
        plt = px.scatter(geodf, x=parameter, y='avg_rop', color_discrete_sequence=[settings['accent']], )
        plt.update_layout(
            xaxis_title_text=parameter,
            yaxis_title_text='Average ROP (ft/min)',
            margin=dict(l=0, r=0, t=5, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor=settings['background-2']
        )

    plt.update_xaxes(
        color=settings['accent']
    )

    plt.update_yaxes(
        color=settings['accent']
    )

    return [plt]


# --- Get Slider Bar Marks ---
def get_bitdiam_marks():
    bit_diam_marks = dict()
    for i in range(min(geodf.bit_diam), max(geodf.bit_diam + 1)):
        bit_diam_marks[i] = str(i) + '\"'
    return bit_diam_marks


def get_depth_marks():
    depth_marks = {}
    for i in range(round(min(geodf.drill_depth), -1), round(max(geodf.drill_depth + 1), -1), 50):
        depth_marks[i] = str(i) + '\''
    return depth_marks


def get_rop_marks():
    rop_marks = {}
    for i in range(round(min(geodf.avg_rop)), round(max(geodf.avg_rop) + 1)):
        rop_marks[i] = str(i)
    return rop_marks


geodf = load_data(fp='data/drillruns.csv')

# --- Configure Layout ---
app.layout = \
    html.Div(
        id='whole-container',
        style={
            'background-color': settings['background'],
        },
        children=[
            # Div for the entire container (background div)
            html.Div(
                style={
                    'background-color': settings['background'],
                    'font-family': settings['font-family'],
                    'margin': '0px 10px 0px 10px'
                },
                children=[
                    # Div for sidebar and figures
                    html.Div(
                        className='row',
                        children=[

                            # Div for sidebar settings
                            html.Div(
                                id='left-sidebar',
                                className='four columns div-user-controls',
                                children=[
                                    html.H4('''DrillGIS: Data Visualization for DrillAI''',
                                            style={
                                                'color': settings['text'],
                                                'margin-top': '5px',
                                                'margin-bottom': '0px',
                                                'text-align': 'center',
                                                'margin-right': '10px'
                                            }),
                                    html.P('Peter Van Katwyk, Advanced Process Solutions, Facebook',
                                           style={
                                               'color': settings['text'],
                                               'text-align': 'center'
                                               # 'border-bottom': '3px solid ' + settings['text'],
                                           }),

                                    # Div for Date Dropdown
                                    html.Div(
                                        id='dates',
                                        className='div-for-dropdown',
                                        children=[
                                            html.P('Date Range',
                                                   style={
                                                       'color': settings['text'],
                                                       'border-top': '3px solid ' + settings['text'],
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.DatePickerRange(
                                                id='date-picker',
                                                start_date=min(geodf.date),
                                                end_date=max(geodf.date),
                                                className='DateRangePickerInput',
                                            ),
                                        ],
                                    ),

                                    # Div for Job Description
                                    html.Div(
                                        id='job-description',
                                        className='div-for-dropdown',
                                        style={'margin-right': '10px'},
                                        children=[
                                            html.P('Job Type',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.Dropdown(
                                                id='job-type-dropdown',
                                                options=[
                                                    {'label': 'Drilling', 'value': 'drilling'},
                                                    {'label': 'Pilot Hole', 'value': 'pilot hole'},
                                                    {'label': 'Backream', 'value': 'backream'}
                                                ],
                                                value=None
                                            ),
                                            html.P('Machine Model',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.Dropdown(
                                                id='machine-model-dropdown',
                                                options=[
                                                    {'label': 'D8x12 HDD', 'value': 'D8x12 HDD'},
                                                    {'label': 'D10x15 S3 HDD', 'value': 'D10x15 S3 HDD'},
                                                    {'label': 'D20x22 S3 HDD', 'value': 'D20x22 S3 HDD'},
                                                    {'label': 'D23x30 S3 HDD', 'value': 'D23x30 S3 HDD'},
                                                    {'label': 'D23x30DR S3 HDD', 'value': 'D23x30DR S3 HDD'},
                                                    {'label': 'D24x40 S3 HDD', 'value': 'D24x40 S3 HDD'},
                                                    {'label': 'D40x55 S3 HDD', 'value': 'D40x55 S3 HDD'},
                                                    {'label': 'D40x55DR S3 HDD', 'value': 'D40x55DR S3 HDD'},
                                                    {'label': 'D60x90 S3 HDD', 'value': 'D60x90 S3 HDD'},
                                                ],
                                                value=None
                                            ),
                                        ],
                                    ),
                                    # Div for Bit Info
                                    html.Div(
                                        id='bit-info',
                                        className='div-for-dropdown',
                                        style={'margin-right': '10px'},
                                        children=[
                                            html.P('Drill Bit Type',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.Dropdown(
                                                id='bit-type',
                                                options=[
                                                    {'label': 'Spoon Bit', 'value': 'spoon'},
                                                    {'label': 'Roller Cone Bit', 'value': 'roller cone'},
                                                    {'label': 'PDC Bit', 'value': 'pdc'}
                                                ],
                                                value=None,
                                            ),
                                            html.P('Bit Diameter',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.RangeSlider(
                                                id='bit-diameter',
                                                min=min(geodf.bit_diam),
                                                max=max(geodf.bit_diam),
                                                marks=get_bitdiam_marks(),
                                                value=[min(geodf.bit_diam), max(geodf.bit_diam)],
                                            ),
                                            html.P('Bore Fluid',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.Dropdown(
                                                id='bore-fluid',
                                                options=[
                                                    {'label': 'Water-Based', 'value': 'water-based'},
                                                    {'label': 'Oil-Based', 'value': 'oil-based'},
                                                    {'label': 'Gaseous', 'value': 'gaseous'}
                                                ],
                                                value=None,
                                            ),
                                        ],
                                    ),
                                    # Div for Drill Metrics
                                    html.Div(
                                        id='metrics',
                                        className='div-for-dropdown',
                                        style={'margin-right': '10px'},
                                        children=[
                                            html.P('Drill Depth',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.RangeSlider(
                                                id='drill-depth',
                                                min=min(geodf.drill_depth),
                                                max=max(geodf.drill_depth),
                                                marks=get_depth_marks(),
                                                value=[min(geodf.drill_depth), max(geodf.drill_depth)],
                                            ),
                                            html.P('Average ROP (ft/min)',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.RangeSlider(
                                                id='avg-rop',
                                                min=min(geodf.avg_rop),
                                                max=max(geodf.avg_rop),
                                                step=0.1,
                                                marks=get_rop_marks(),
                                                value=[min(geodf.avg_rop), max(geodf.avg_rop)],
                                            ),
                                            html.P('Soil Type',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-top': '10px',
                                                       'margin-bottom': '0px'
                                                   }),
                                            dcc.Dropdown(
                                                id='soil-type',
                                                options=[
                                                    {'label': 'Gravel', 'value': 'Gravel'},
                                                    {'label': 'Sandy Gravel', 'value': 'Sandy Gravel'},
                                                    {'label': 'Loamy Gravel', 'value': 'Loamy Gravel'},
                                                    {'label': 'Silty Gravel', 'value': 'Silty Gravel'},
                                                    {'label': 'Sand', 'value': 'Sand'},
                                                    {'label': 'Gravelly Sand', 'value': 'Gravely Sand'},
                                                    {'label': 'Loamy Sand', 'value': 'Loamy Sand'},
                                                    {'label': 'Silty Sand', 'value': 'Silty Sand'},
                                                    {'label': 'Loam', 'value': 'Loam'},
                                                    {'label': 'Gravelly Loam', 'value': 'Gravely Loam'},
                                                    {'label': 'Sandy Loam', 'value': 'Sandy Loam'},
                                                    {'label': 'Silty Loam', 'value': 'Silty Loam'},
                                                    {'label': 'Silt', 'value': 'Silt'},
                                                    {'label': 'Gravelly Silt', 'value': 'Gravely Silt'},
                                                    {'label': 'Loamy Silt', 'value': 'Loamy Silt'},
                                                    {'label': 'Sandy Silt', 'value': 'Sandy Silt'},
                                                ],
                                                placeholder='Select...',
                                                # value=list(geodf.mod_class.unique()),
                                                value=None

                                                # multi=True
                                            ),
                                        ],
                                    ),

                                    # Div for Send to CSV button
                                    html.Div(
                                        id='to-csv-div',
                                        style={
                                            'margin-right': '10px'
                                        },
                                        children=[
                                            html.Button('Send Data to CSV',
                                                        id='to-csv-button',
                                                        style={
                                                            'margin-top': '20px',
                                                            'width': '100%',
                                                            'border': '1px solid ' + settings['text']
                                                        }),
                                            dcc.Download(id='download-csv')
                                        ],
                                    ),

                                    # Div for bottom
                                    html.Div(
                                        id='bottom-sidebar-div',
                                        className='div-for-dropdown',
                                        children=[
                                            #  -- For Future Release --
                                            # Div for changing theme
                                            # html.Div(
                                            #     id='theme-div',
                                            #     className='div-for-dropdown',
                                            #     style={
                                            #         'width': '40%'
                                            #     },
                                            #     children=[
                                            #         html.P('Select Theme',
                                            #                style={
                                            #                    'color': settings['text'],
                                            #                    'margin-top': '110px',
                                            #                    'margin-bottom': '0px'
                                            #                }),
                                            #         dcc.Dropdown(
                                            #             id='theme-dropdown',
                                            #             options=[
                                            #                 {'label': 'Default', 'value': 'default'},
                                            #                 {'label': 'Dark', 'value': 'dark'},
                                            #                 {'label': 'Light', 'value': 'light'},
                                            #             ],
                                            #             value='default'
                                            #         )
                                            #     ]
                                            # ),

                                            # Div for text at the bottom of the sidebar
                                            html.Div(
                                                id='bottom-text',
                                                className='text-padding',
                                                children=[
                                                    html.P('DrillGIS v1.0.0',
                                                           style={
                                                               'margin-bottom': '0px',
                                                               'margin-top': '150px',
                                                               'color': settings['text']
                                                           }),
                                                    html.P('''Change the parameters listed above to subset the current 
                                            drilling data. The map and histogram will automatically update to show 
                                            the parameters that were selected above, whereas the ROP vs Parameter 
                                            comparison shows trends in the entire  dataset. This tool is property of 
                                            Advanced Process Solutions & Facebook.''',
                                                           style={
                                                               'font-size': '10px',
                                                               'color': settings['text'],
                                                               'margin-right': '10px',
                                                           })
                                                ],
                                            ),
                                        ]
                                    ),
                                ],
                            ),

                            # Div for right figure container
                            html.Div(
                                id='right-graphs',
                                className='eight columns div-for-charts bg-grey',
                                style={
                                    'border-left': '3px solid ' + settings['text'],
                                    'margin-left': '0px'

                                },
                                children=[
                                    # Div for map
                                    html.Div(
                                        id='map-div',
                                        className='row graph-top',
                                        style={
                                            'margin-left': '5px'
                                        },
                                        children=[
                                            # Div for the drill counter at the top right
                                            html.Div(
                                                id='drill-count',
                                                style={
                                                    'color': settings['text'],
                                                    'text-align': 'right'
                                                    # 'width': '325px',
                                                    # 'border': '0px solid ' + settings['text'],
                                                    # 'text-align': 'center'
                                                }
                                            ),
                                            dcc.Graph(
                                                id='map',
                                                className='chart-graph',
                                            ),
                                        ],
                                    ),
                                    # Div for graphs below
                                    html.Div(
                                        id='graphs-div',
                                        className='row',
                                        style={
                                            'margin-left': '5px'
                                        },
                                        children=[
                                            # Div for bottom-left histogram
                                            html.Div(
                                                id='left-bottom-graph',
                                                className='six columns',
                                                style={
                                                    'margin-left': '10px'
                                                },
                                                children=[
                                                    html.Br(),
                                                    html.P('Average ROP Histogram',
                                                           style={
                                                               'color': settings['text']
                                                           }),
                                                    dcc.Input(
                                                        id='num-bins',
                                                        type='number',
                                                        placeholder='# Histogram Bins',
                                                    ),
                                                    dcc.Graph(
                                                        id='rop-hist',
                                                    )
                                                ]
                                            ),
                                            # Div for bottom right relationship graphs
                                            html.Div(
                                                id='right-bottom-graph',
                                                className='six columns',
                                                style={
                                                    'margin-left': '20px'
                                                },
                                                children=[
                                                    html.Br(),
                                                    html.P('ROP vs Parameter Comparison',
                                                           style={
                                                               'color': settings['text']
                                                           }),
                                                    # Div for parameter dropdown
                                                    html.Div(
                                                        id='parameter-dropdown-div',
                                                        className='div-for-dropdown',
                                                        style={
                                                            'width': '50%',
                                                        },
                                                        children=[
                                                            dcc.Dropdown(
                                                                id='parameter-dropdown',
                                                                options=[
                                                                    {'label': 'Job Type', 'value': 'job_type'},
                                                                    {'label': 'Machine Model',
                                                                     'value': 'machine_model'},
                                                                    {'label': 'Drill Bit Type', 'value': 'drill_type'},
                                                                    {'label': 'Bit Diameter', 'value': 'bit_diam'},
                                                                    {'label': 'Bore Fluid', 'value': 'bore_fluid'},
                                                                    {'label': 'Drill Depth', 'value': 'drill_depth'},
                                                                    {'label': 'Soil Type', 'value': 'mod_class'},
                                                                ],
                                                                placeholder='Select a Parameter'
                                                            ),
                                                        ],
                                                    ),

                                                    dcc.Graph(
                                                        id='rop-comparison',
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


# Callback for updating the map and histogram
@app.callback(
    [Output(component_id='map', component_property='figure'),
     Output(component_id='drill-count', component_property='children'),
     Output(component_id='rop-hist', component_property='figure'),
     Output(component_id='download-csv', component_property='data')],
    [Input(component_id='date-picker', component_property='start_date'),
     Input(component_id='date-picker', component_property='end_date'),
     Input(component_id='job-type-dropdown', component_property='value'),
     Input(component_id='machine-model-dropdown', component_property='value'),
     Input(component_id='bit-type', component_property='value'),
     Input(component_id='bit-diameter', component_property='value'),
     Input(component_id='bore-fluid', component_property='value'),
     Input(component_id='drill-depth', component_property='value'),
     Input(component_id='avg-rop', component_property='value'),
     Input(component_id='soil-type', component_property='value'),
     Input(component_id='num-bins', component_property='value'),
     Input(component_id='to-csv-button', component_property='n_clicks')],
    [State(component_id='to-csv-button', component_property='n_clicks')]
)
def update_map(start_date, end_date, job_type, machine_model, bit_type, bit_diam, bore_fluid, drill_depth,
               avg_rop, soil_type, num_bins, download_click, prev_n_click):
    """update_map
    Inputs: All buttons from dashboard
    Outputs: Map, data count, histogram, and download
    Description: Uses all the button inputs to subset the graph and display the subset on the map and histogram. It also
    counts the rows of the data to display how many data points are being shown, and downloads the subset data if the
    data is requested throught the Send to CSV button."""

    # Format dates
    start_date_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    geodf['datetime'] = pd.to_datetime(geodf.date)

    # If there is no input to the button, graph all of the values of the parameter (all the data)
    if job_type is None:
        job_type = list(geodf.job_type.unique())
    else:
        job_type = [job_type]
    if machine_model is None:
        machine_model = list(geodf.machine_model.unique())
    else:
        machine_model = [machine_model]
    if bit_type is None:
        bit_type = list(geodf.drill_type.unique())
    else:
        bit_type = [bit_type]
    if bore_fluid is None:
        bore_fluid = list(geodf.bore_fluid.unique())
    else:
        bore_fluid = [bore_fluid]
    if soil_type is None:
        soil_type = list(geodf.mod_class.unique())
    else:
        soil_type = [soil_type]
    if num_bins is None:
        num_bins = 20

    # Subset data based on button inputs
    df = geodf.loc[
        (geodf.datetime >= start_date_datetime) &
        (geodf.datetime <= end_date_datetime) &
        (geodf.job_type.isin(job_type)) &
        (geodf.machine_model.isin(machine_model)) &
        (geodf.drill_type.isin(bit_type)) &
        (geodf.bit_diam >= bit_diam[0]) &
        (geodf.bit_diam <= bit_diam[1]) &
        (geodf.bore_fluid.isin(bore_fluid)) &
        (geodf.drill_depth >= drill_depth[0]) &
        (geodf.drill_depth <= drill_depth[1]) &
        (geodf.avg_rop >= avg_rop[0]) &
        (geodf.avg_rop <= avg_rop[1]) &
        (geodf.mod_class.isin(soil_type))
        ]

    # If the data is empty (there are no runs with the parameters specified), make the figures blank
    if len(df) == 0:
        map = build_map(geodf, empty=True)
        hist = build_histogram(geodf, num_bins=num_bins, empty=True)
        count = 'There are no drill runs during the specified time.'

    else:
        try:
            map = build_map(df, empty=False)
            hist = build_histogram(df, num_bins=num_bins, empty=False)
            count = f'Currently showing {len(df)} drill run(s).'

        except KeyError:
            map = build_map(geodf, empty=True)
            hist = build_histogram(geodf, num_bins=num_bins, empty=True)
            count = 'There are no drill runs during the specified time.'

    # Set up callback context to determine the button that was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # If the to-csv button has been clicked and the new click was the to-csv button again,
    # make the previous and current clicks different by one click
    if prev_n_click is not None and button_id == 'to-csv-button':
        prev_n_click = prev_n_click - 1

    # If the to-csv button has been clicked and the previous vs current click numbers are different,
    # download the csv
    if download_click is not None and prev_n_click != download_click:
        return map, count, hist, dcc.send_data_frame(df.to_csv, 'DrillGIS.csv')
    else:
        return map, count, hist, None

# Callback for updating relational graph in the bottom-right
@app.callback(
    [Output(component_id='rop-comparison', component_property='figure')],
    [Input(component_id='parameter-dropdown', component_property='value')]
)
def update_comparison(parameter):
    fig = build_parameter_graph(parameter)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)