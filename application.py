import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from datetime import datetime
import boto3
import requests
import json
from boto3.dynamodb.conditions import Attr
import numpy as np

settings = {
    'background': '#aad3df',
    'text': '#0f3057',
    'accent': '#008891',
    'background-2': '#e7e7de',
    'company': '#2dcf11',
    'map_zoom': 3.25,
    'font-family': 'Open Sans, sans-serif'
}

app = dash.Dash(
    name=__name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    title='DrillGIS',
    assets_folder="static", # Elastic Beanstalk recognizes "static folder"
    assets_url_path="static"
)
application = app.server


def authenticate(pin):
    """
    :param pin: Operator/Company pin to be validated (int or string)
    :return: authenticated (boolean saying whether it has been authenticated or not)
    status (dictionary containing account information)
    """
    api = r'https://dm9yykm2b4.execute-api.us-west-1.amazonaws.com/alpha/authentication'
    data = {
        "pin": str(pin)
    }
    data = json.dumps(data)
    response = requests.post(api, data=data)
    try:
        response_dict = json.loads(response.text)
        status = {'company': response_dict['company'], 'company_pin': response_dict['company_pin'],
                  'acc_type': response_dict['acc_type'], "operator_pin": pin}
        authenticated = True
    except TypeError:
        status = "Unable to authenticate PIN."
        authenticated = False

    return authenticated, status


def get_company_pins():
    """
    :return: companies (dictionary of rows of companies to be used in classify_pin())
    """
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table = dynamodb.Table('auth')
    response = table.scan(
        FilterExpression=Attr("acc_type").eq("company")
    )
    companies = response['Items']
    return companies


def classify_pin(company_pin, companies):
    """

    :param company_pin: Company pin being used to classify rows by company
    :param companies: Dictionary of unique companies
    :return:
    """
    out = "Other"
    for company in companies:
        if company['company_pin'] == str(company_pin):
            out = company['company']
    return out


def load_data():
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table = dynamodb.Table('drill-data')
    response = table.scan()
    data = pd.DataFrame(response['Items'])
    companies = get_company_pins()
    data['company'] = data['job-id'].apply(lambda x: classify_pin(x[:6], companies))
    data['operator_pin'] = data['job-id'].apply(lambda x: x[7:13])
    for column in ['drill_depth', 'bit_diam']:
        data[str(column)] = data[str(column)].apply(int)
    for column in ['lon', 'lat', 'avg_rop']:
        data[str(column)] = data[str(column)].apply(float)
    return data


# --- Functions to build graphics ---
def build_map(data, empty=False, color=None, company=None):
    # Tokens for custom maps ---
    # acccess_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"
    # mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
    # token = "pk.eyJ1IjoicHZhbmthdHd5ayIsImEiOiJja29hbmF3bTMwMnNxMnVsaHEya3J1bjBmIn0.-_ESAo1-Qogpzv66fVrh5Q"
    labels = {'Drillrun Operator': 'Operator', 'company_int': 'Operator Code', 'lat': 'Latitude',
              'lon': 'Longitude', 'date': 'Date', 'machine_model': 'Machine Model', 'drill_type': 'Bit Type',
              'bit_diam': 'Bit Diameter (in)', 'usda_class': 'Soil Classification (USDA)',
              'mod_class': 'Soil Classification (Model)',
              'weather': 'Temp (deg F)', 'avg_rop': 'Average ROP (ft/min)', 'bore_fluid': 'Bore Fluid',
              'drill_depth': 'Drill Depth (ft)',
              'job_type': 'Job Type'}
    opacity = 0 if empty else 1
    if color is None:
        map = px.scatter_mapbox(data,
                                lat=data.lat, lon=data.lon,
                                labels=labels,
                                hover_data=['date', 'job_type', "machine_model", "drill_type", 'bit_diam', "usda_class",
                                            "mod_class", "bore_fluid", "drill_depth", "avg_rop"],
                                zoom=settings['map_zoom'],
                                color_discrete_sequence=[settings['accent']],
                                opacity=opacity
                                )
    else:
        map = px.scatter_mapbox(data,
                                lat=data.lat, lon=data.lon,
                                hover_data=['date', 'job_type', "machine_model", "drill_type", 'bit_diam', "usda_class",
                                            "mod_class", "bore_fluid", "drill_depth", "avg_rop"],
                                zoom=settings['map_zoom'],
                                labels=labels,
                                opacity=opacity,
                                color=data['Drillrun Operator'],
                                color_discrete_map={
                                    "Other": "grey",
                                    company: color
                                },
                                size=data.company_int,
                                size_max=8
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
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        legend_traceorder="reversed",
    )

    return map


def build_histogram(data, num_bins=10, empty=False, company=None, color=None):
    opacity = 0 if empty else 1
    if company is not None:
        hist = px.histogram(data,
                            x='avg_rop',
                            nbins=num_bins,
                            color=data['Drillrun Operator'],
                            color_discrete_map={
                                "Other": "grey",
                                company: color
                            },
                            # opacity=opacity,
                            barmode='overlay'
                            )
    else:
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
        plot_bgcolor=settings['background-2'],
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        legend_traceorder="reversed"
    )
    hist.update_xaxes(
        # range=[0, 5.5],
        color=settings['accent']
    )

    hist.update_yaxes(
        color=settings['accent']
    )

    return hist


def build_dist_plot(data, state, num_bins=10, company=False, color=None):
    import plotly.figure_factory as ff
    if not company:
        x1 = data.avg_rop

        hist_data = [x1]

        group_labels = ['All Data']
        colors = [settings['accent']]
    else:
        x1 = data.avg_rop.loc[data['Drillrun Operator'] == state]
        x2 = data.avg_rop.loc[data['Drillrun Operator'] == 'Other']

        hist_data = [x1, x2]

        group_labels = [state, 'Other']
        colors = [color, 'grey']

    # Create distplot with curve_type set to 'normal'
    fig = ff.create_distplot(hist_data, group_labels, colors=colors,
                             bin_size=1 / num_bins * 4, show_rug=False)
    fig.update_layout(
        bargap=0.025,
        xaxis_title_text='Average ROP (ft/min)',
        yaxis_title_text='Distribution',
        margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor=settings['background-2'],
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        legend_traceorder="reversed",
        legend_title_text="Drillrun Operator"
    )
    fig.update_xaxes(
        # range=[0, 5.5],
        color=settings['accent']
    )

    fig.update_yaxes(
        color=settings['accent']
    )
    return fig


def build_parameter_graph(data, parameter, company=None, color=None):
    if parameter is None:
        parameter = 'mod_class'
        label = 'Soil Type'
    else:
        label = parameter.title().replace('_', ' ')

    if company is not None:
        if parameter in ('job_type', 'machine_model', 'drill_type', 'bit_diam', 'bore_fluid', 'mod_class'):
            plt = px.box(data,
                         x=parameter,
                         y='avg_rop',
                         color=data['Drillrun Operator'],
                         color_discrete_map={
                             "Other": "grey",
                             company: color
                         }
                         )
        else:
            # Else (the parameter is continuous), use scatterplot
            plt = px.scatter(data,
                             x=parameter,
                             y='avg_rop',
                             color=data['Drillrun Operator'],
                             color_discrete_map={
                                 "Other": "grey",
                                 company: color
                             }
                             )
    else:
        # If the parameter is categorical, use boxplot
        if parameter in ('job_type', 'machine_model', 'drill_type', 'bit_diam', 'bore_fluid', 'mod_class'):
            plt = px.box(data, x=parameter, y='avg_rop', color_discrete_sequence=[settings['accent']])
        else:
            # Else (the parameter is continuous), use scatterplot
            plt = px.scatter(data, x=parameter, y='avg_rop', color_discrete_sequence=[settings['accent']], )

    plt.update_layout(
        xaxis_title_text=label,
        yaxis_title_text='Average ROP (ft/min)',
        margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor=settings['background-2'],
        legend_traceorder="reversed",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
    )
    plt.update_xaxes(
        color=settings['accent']
    )

    plt.update_yaxes(
        color=settings['accent']
    )

    return [plt]


# --- Get Slider Bar Marks ---
# TODO: Probably can avoid these functions using list comprehension
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


geodf = load_data()

# --- Configure Layout ---
app.layout = \
    html.Div(
        id='whole-container',
        style={
            'background-color': settings['background'],
        },
        children=[
            dcc.Store(
                id='store-state'
            ),
            dcc.Store(
                id='store-color'
            ),
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
                                    html.P('Advanced Process Solutions, Middle Mile Infrastructure',
                                           style={
                                               'color': settings['text'],
                                               'text-align': 'center',
                                               'margin-right': '20px'
                                               # 'border-bottom': '3px solid ' + settings['text'],
                                           }),
                                    html.P('User Credentials',
                                           style={
                                               'border-top': '3px solid ' + settings['text'],
                                               'margin-top': '15px',
                                               'margin-bottom': '0px',
                                           },
                                           ),
                                    html.Div(
                                        id='div-for-credentials',
                                        className='row',
                                        style={
                                            'margin-right': '10px',
                                        },
                                        children=[
                                            html.Div(
                                                id='div-for-pin',
                                                className='six columns',
                                                children=[
                                                    dcc.Input(
                                                        id='pin',
                                                        # type='password',
                                                        placeholder='User PIN',
                                                        style={
                                                            'width': '100%'
                                                        },
                                                        value=None
                                                    )
                                                ],
                                            ),
                                            html.Div(
                                                id='div-for-login',
                                                # style={'margin-right': '5px'},
                                                className='six columns',
                                                children=[
                                                    html.Button('Log In',
                                                                id='log-in',
                                                                style={
                                                                    'width': '100%',
                                                                    'border': '1px solid ' + settings['text'],
                                                                },
                                                                ),
                                                ],
                                            ),
                                            html.Div(
                                                id='current-account',
                                                style={
                                                    'color': settings['text'],
                                                }
                                            )
                                        ],
                                    ),

                                    # Div for Date Dropdown
                                    html.Div(
                                        id='dates',
                                        className='div-for-dropdown',
                                        children=[
                                            html.P('Date Range',
                                                   style={
                                                       'color': settings['text'],
                                                       'margin-bottom': '0px',
                                                       'margin-top': '10px'
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
                                                    {'label': x.title(), 'value': x.lower()} for x in set(geodf.job_type)
                                                ],
                                                # [
                                                #     {'label': 'Drilling', 'value': 'drilling'},
                                                #     {'label': 'Pilot Hole', 'value': 'pilot hole'},
                                                #     {'label': 'Backream', 'value': 'backream'},
                                                #     {'label': 'Other', 'value': 'other'}
                                                # ],
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
                                                options=[{'label': x, 'value': x} for x in set(geodf.machine_model)],
                                                # [
                                                #     {'label': 'D8x12 HDD', 'value': 'D8x12 HDD'},
                                                #     {'label': 'D10x15 S3 HDD', 'value': 'D10x15 S3 HDD'},
                                                #     {'label': 'D20x22 S3 HDD', 'value': 'D20x22 S3 HDD'},
                                                #     {'label': 'D23x30 S3 HDD', 'value': 'D23x30 S3 HDD'},
                                                #     {'label': 'D23x30DR S3 HDD', 'value': 'D23x30DR S3 HDD'},
                                                #     {'label': 'D24x40 S3 HDD', 'value': 'D24x40 S3 HDD'},
                                                #     {'label': 'D40x55 S3 HDD', 'value': 'D40x55 S3 HDD'},
                                                #     {'label': 'D40x55DR S3 HDD', 'value': 'D40x55DR S3 HDD'},
                                                #     {'label': 'D60x90 S3 HDD', 'value': 'D60x90 S3 HDD'},
                                                #     {'label': 'Other', 'value': 'other'}
                                                # ],
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
                                                    {'label': x.title(), 'value': x.lower()} for x in set(geodf.drill_type)
                                                ],
                                                # [
                                                #     {'label': 'Spoon Bit', 'value': 'spoon'},
                                                #     {'label': 'Roller Cone Bit', 'value': 'roller cone'},
                                                #     {'label': 'PDC Bit', 'value': 'pdc'},
                                                #     {'label': 'Other', 'value': 'other'}
                                                # ],
                                                value=None,
                                            ),
                                            html.P('Bit Diameter (in)',
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
                                                    {'label': x.title(), 'value': x.lower()} for x in set(geodf.bore_fluid)
                                                ],
                                                # [
                                                #     {'label': 'Water-Based', 'value': 'water-based'},
                                                #     {'label': 'Oil-Based', 'value': 'oil-based'},
                                                #     {'label': 'Gaseous', 'value': 'gaseous'},
                                                #     {'label': 'Other', 'value': 'other'}
                                                # ],
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
                                            html.P('Drill Depth (ft)',
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
                                            html.P('Average Rate of Penetration (ROP) (ft/min)',
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
                                                    {'label': x.title(), 'value': x.lower()} for x in set(geodf.mod_class)
                                                ],
                                                # [
                                                #     {'label': 'Gravel', 'value': 'Gravel'},
                                                #     {'label': 'Sandy Gravel', 'value': 'Sandy Gravel'},
                                                #     {'label': 'Loamy Gravel', 'value': 'Loamy Gravel'},
                                                #     {'label': 'Silty Gravel', 'value': 'Silty Gravel'},
                                                #     {'label': 'Sand', 'value': 'Sand'},
                                                #     {'label': 'Gravelly Sand', 'value': 'Gravely Sand'},
                                                #     {'label': 'Loamy Sand', 'value': 'Loamy Sand'},
                                                #     {'label': 'Silty Sand', 'value': 'Silty Sand'},
                                                #     {'label': 'Loam', 'value': 'Loam'},
                                                #     {'label': 'Gravelly Loam', 'value': 'Gravely Loam'},
                                                #     {'label': 'Sandy Loam', 'value': 'Sandy Loam'},
                                                #     {'label': 'Silty Loam', 'value': 'Silty Loam'},
                                                #     {'label': 'Silt', 'value': 'Silt'},
                                                #     {'label': 'Gravelly Silt', 'value': 'Gravely Silt'},
                                                #     {'label': 'Loamy Silt', 'value': 'Loamy Silt'},
                                                #     {'label': 'Sandy Silt', 'value': 'Sandy Silt'},
                                                # ],
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
                                                    html.P('DrillGIS v1.2.1 - © 2021, All rights reserved.',
                                                           style={
                                                               'margin-bottom': '0px',
                                                               'margin-top': '35px',
                                                               'color': settings['text']
                                                           }),
                                                    html.P('Website Developer: Peter Van Katwyk',
                                                           style={
                                                               'font-size': '12px',
                                                               'margin-bottom': '0px',
                                                               'color': settings['text']
                                                           }),
                                                    html.P('''Change the parameters listed above to subset the current 
                                            drilling data. The map and histogram will automatically update to show 
                                            the parameters that were selected above, whereas the ROP vs Parameter 
                                            comparison shows trends in the entire  dataset. This tool is property of 
                                            Advanced Process Solutions & Middle Mile Infrastructure.''',
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
                                                    html.P('Average Rate of Penetration Histogram',
                                                           style={
                                                               'color': settings['text']
                                                           }),
                                                    html.Div(
                                                        id='div-for-hist-settings',
                                                        className='row',
                                                        children=[
                                                            dcc.Input(
                                                                id='num-bins',
                                                                type='number',
                                                                className='six columns',
                                                                placeholder='# Histogram Bins',
                                                            ),
                                                            dcc.Dropdown(
                                                                id='hist-dist',
                                                                className='six columns',
                                                                style={
                                                                    'width': '100%',
                                                                    'margin-left': '10px'
                                                                },
                                                                placeholder='Select Plot Type',
                                                                options=[
                                                                    {'label': 'Histogram', 'value': 'hist_plot'},
                                                                    {'label': 'Distribution', 'value': 'dist_plot'},
                                                                ],
                                                                value='hist_plot'
                                                            )
                                                        ]
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
                                                    html.P('Rate of Penetration vs Parameter Comparison',
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
     Output(component_id='download-csv', component_property='data'),
     Output(component_id='current-account', component_property='children'),
     Output(component_id='store-state', component_property='data'),
     Output(component_id='store-color', component_property='data')],
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
     Input(component_id='to-csv-button', component_property='n_clicks'),
     Input(component_id='pin', component_property='value'),
     Input(component_id='log-in', component_property='n_clicks'),
     Input(component_id='hist-dist', component_property='value')
     ],
    [State(component_id='to-csv-button', component_property='n_clicks'),
     State(component_id='log-in', component_property='n_clicks')]
)
def update_map(start_date, end_date, job_type, machine_model, bit_type, bit_diam, bore_fluid, drill_depth,
               avg_rop, soil_type, num_bins, download_click, pin, login_clicks, hist_dist, prev_n_click,
               prev_log_click):
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
        num_bins = 10

    # Set up callback context to determine the button that was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    authenticated, status = authenticate(pin)
    company_name = status['company'] if authenticated else None
    pin_exists = True if pin not in (None, '') else False
    login = True if login_clicks is not None and int(login_clicks) > 0 else False

    company_color_dict = {
        "Company 1": '#2dcf11',
        "Company 2": '#4287f5',
        "Company 3": '#db881a',
        "Company 4": '#db1a20',
    }

    # if prev_log_click is not None and button_id == 'log-in':
    #     prev_log_click -= 1
    login_clicked = True if login_clicks is not None and prev_log_click != login_clicks else False
    # login_clicked = True if login_clicks is not None else False

    # if authenticated and pin_exists and login and login_clicked:
    if authenticated and pin_exists and login:
        operator = True if status['acc_type'] == "operator" else False
        current_account = 'Logged in to: ' + str(company_name) + ' (Operator ' + str(status['operator_pin']) + ')' \
            if operator else 'Logged in to: ' + str(company_name) + ' (Admin Account)'

        if operator:
            state = status['operator_pin']
        else:
            state = company_name
        company_color = company_color_dict[str(company_name)]
    # elif not authenticated and pin_exists and login and login_clicked:
    elif not authenticated and pin_exists and login:
        current_account = status
        company_color = None
        state = None
    else:
        current_account = "Enter user PIN."
        company_color = None
        state = None

    # Subset data based on button inputs
    # if username is None and password is None:
    if state is not None:
        if operator:
            geodf['Drillrun Operator'] = geodf['operator_pin'].apply(lambda x: str(state) if x == state else "Other")
            geodf['operator_class'] = geodf['operator_pin'].apply(lambda x: x if x == state else "Other")
        else:
            geodf['Drillrun Operator'] = geodf['company'].apply(lambda x: state if x in state else "Other")
            geodf['operator_class'] = np.array(geodf.company == state) * geodf['operator_pin']
        geodf['company_int'] = geodf['Drillrun Operator'].apply(lambda x: 1 if x in "Other" else 2)

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

    if state is not None:
        # If the data is empty (there are no runs with the parameters specified), make the figures blank
        if len(df) == 0:
            map = build_map(geodf, empty=True)
            hist = build_histogram(geodf, num_bins=num_bins, empty=True)
            count = 'There are no drill runs during the specified time.'

        else:
            try:

                map = build_map(df, empty=False, color=company_color, company=state)
                if hist_dist == 'dist_plot':
                    try:
                        hist = build_dist_plot(df, state=state, num_bins=num_bins, company=True, color=company_color)
                    except ValueError:
                        hist = build_histogram(geodf, num_bins=num_bins, empty=True)
                else:
                    hist = build_histogram(df, num_bins=num_bins, empty=False, company=state, color=company_color)

                count = f'Currently showing {len(df)} drill run(s).'

            except KeyError:
                map = build_map(geodf, empty=True)
                hist = build_histogram(geodf, num_bins=num_bins, empty=True)
                count = 'There are no drill runs during the specified time.'
    else:
        # If the data is empty (there are no runs with the parameters specified), make the figures blank
        if len(df) == 0:
            map = build_map(geodf, empty=True)
            hist = build_histogram(geodf, num_bins=num_bins, empty=True)
            count = 'There are no drill runs during the specified time.'

        else:
            try:
                map = build_map(df, empty=False)
                if hist_dist == 'dist_plot':
                    hist = build_dist_plot(df, state=state, num_bins=num_bins, company=False)
                else:
                    hist = build_histogram(df, num_bins=num_bins, empty=False, company=None)
                count = f'Currently showing {len(df)} drill run(s).'

            except KeyError:
                map = build_map(geodf, empty=True)
                hist = build_histogram(geodf, num_bins=num_bins, empty=True)
                count = 'There are no drill runs during the specified time.'

    try:
        df_to_csv = df.drop(columns=['company', 'datetime', 'company_int'])
    except:
        df_to_csv = df.drop(columns=['company', 'datetime'])

    # If the to-csv button has been clicked and the new click was the to-csv button again,
    # make the previous and current clicks different by one click
    if prev_n_click is not None and button_id == 'to-csv-button':
        prev_n_click -= - 1

    # If the to-csv button has been clicked and the previous vs current click numbers are different,
    # download the csv
    if download_click is not None and prev_n_click != download_click:
        send_to_csv = dcc.send_data_frame(df_to_csv.to_csv, 'DrillGIS.csv')
    else:
        send_to_csv = None

    return map, count, hist, send_to_csv, current_account, state, company_color


# Callback for updating relational graph in the bottom-right
@app.callback(
    [Output(component_id='rop-comparison', component_property='figure')],
    [Input(component_id='parameter-dropdown', component_property='value'),
     Input(component_id='store-state', component_property='data'),
     Input(component_id='store-color', component_property='data')]
)
def update_comparison(parameter, state, company_color):
    if state is not None:
        fig = build_parameter_graph(data=geodf, parameter=parameter, company=state, color=company_color)
    else:
        fig = build_parameter_graph(data=geodf, parameter=parameter, company=state)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
