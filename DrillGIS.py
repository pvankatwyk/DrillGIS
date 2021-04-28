import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from datetime import datetime

colors = {
    'background': '#aad3df',
    'text': '#002b63'
}

app = dash.Dash(__name__)
server = app.server

geodf = pd.read_csv('data/drillruns.csv')
fig = px.scatter_mapbox(geodf,
                        lat=geodf.lat, lon=geodf.lon,
                        hover_name="job_type",
                        hover_data=["date", "drill_type", "usda_class", "mod_class"],
                        # color_discrete_sequence=[colors['background']],
                        color='job_type',
                        size='bit_diam',
                        zoom=2,
                        # height=400,
                        )
fig.update_layout(mapbox_style="open-street-map",
                  margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  plot_bgcolor=colors['background'],
                  paper_bgcolor=colors['background'],
                  font_color=colors['text'],
                  legend=dict(
                      yanchor="top",
                      y=0.99,
                      xanchor="left",
                      x=0.01
                  )
                  )

slider_marks = dict()
for i in range(min(geodf.bit_diam), max(geodf.bit_diam + 1)):
    slider_marks[i] = str(i) + ' in'

app.layout = html.Div(className='container',
                      children=[
                          # SIDEBAR
                          html.Div([
                              html.H1(children='DrillGIS',
                                      className='title',
                                      ),
                              html.Div(children='Drillsite Visualization from DrillAI deployment',
                                       style={
                                           'textAlign': 'left',
                                           'color': colors['text'],
                                           'padding-right': '10px',
                                           'padding-left': '5px'
                                       }
                                       ),
                              html.Div('Peter Van Katwyk', className='author'),
                              html.Div('Select a Date Range',
                                       className='DatePickerTitle',
                                       style={
                                           'padding-left': '5px'
                                       }
                                       ),
                              dcc.DatePickerRange(
                                  id='date-picker',
                                  start_date=min(geodf.date),
                                  end_date=max(geodf.date),
                                  className='DateRangePickerInput',
                              ),
                              html.Div(
                                  id='output-date-picker',
                                  style={
                                      'padding-bottom': '20px',
                                      'padding-left': '5px'
                                  }
                              ),
                              html.Div('Job Type',
                                       style={
                                           'padding-left': '5px'
                                       }),
                              dcc.Dropdown(
                                  id='job-type-dropdown',
                                  options=[
                                      {'label': 'Drilling', 'value': 'drilling'},
                                      {'label': 'Enlarging', 'value': 'enlarging'},
                                      {'label': 'Backream', 'value': 'backream'}
                                  ],
                                  value=None
                              ),

                              html.Div('Drill Bit Type',
                                       style={
                                           'padding-top': '20px',
                                           'padding-left': '5px'
                                       }),
                              dcc.Dropdown(
                                  id='bit-type-dropdown',
                                  options=[
                                      {'label': 'Spoon Bit', 'value': 'spoon'},
                                      {'label': 'Roller Cone Bit', 'value': 'roller cone'},
                                      {'label': 'PDC Bit', 'value': 'pdc'}
                                  ],
                                  value=None

                              ),
                              html.Div('Bit Diameter',
                                       style={
                                           'padding-top': '20px',
                                           'padding-left': '5px'
                                       }),
                              dcc.RangeSlider(
                                  id='range-slider',
                                  min=min(geodf.bit_diam),
                                  max=max(geodf.bit_diam),
                                  step=1,
                                  marks=slider_marks,
                                  value=[4, 9]

                              )
                          ], className='sidebar'),

                          # MAP
                          html.Div([
                              # dcc.Graph(
                              #     id='example-graph',
                              #     figure=fig,
                              #     style={
                              #         'height': '100vh'
                              #     },
                              #     responsive=True,
                              #     config={'autosizable': True}
                              # )

                              dcc.Graph(id='drillgis-map')
                          ], className='graph')

                      ])


@app.callback(
    [Output(component_id='output-date-picker', component_property='children'),
     Output(component_id='drillgis-map', component_property='figure')],
    [Input(component_id='date-picker', component_property='start_date'),
     Input(component_id='date-picker', component_property='end_date'),
     Input(component_id='job-type-dropdown', component_property='value'),
     Input(component_id='bit-type-dropdown', component_property='value'),
     Input(component_id='range-slider', component_property='value')]
)
def update_output(start_date, end_date, job_type, bit_type, bit_diam):
    start_date_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    geodf['datetime'] = pd.to_datetime(geodf.date)
    if job_type is None and bit_type is not None:
        df = geodf.loc[(geodf.datetime >= start_date_datetime) & (geodf.datetime <= end_date_datetime) &
                       (geodf.drill_type == bit_type) &
                       (geodf.bit_diam >= bit_diam[0]) & (geodf.bit_diam <= bit_diam[1])]
    elif bit_type is None and job_type is not None:
        df = geodf.loc[(geodf.datetime >= start_date_datetime) & (geodf.datetime <= end_date_datetime) &
                       (geodf.job_type == job_type) &
                       (geodf.bit_diam >= bit_diam[0]) & (geodf.bit_diam <= bit_diam[1])]
    elif bit_type is None and job_type is None:
        df = geodf.loc[(geodf.datetime >= start_date_datetime) & (geodf.datetime <= end_date_datetime) &
                       (geodf.bit_diam >= bit_diam[0]) & (geodf.bit_diam <= bit_diam[1])]
    else:
        df = geodf.loc[(geodf.datetime >= start_date_datetime) & (geodf.datetime <= end_date_datetime) &
                       (geodf.job_type == job_type) & (geodf.drill_type == bit_type) &
                       (geodf.bit_diam >= bit_diam[0]) & (geodf.bit_diam <= bit_diam[1])]

    if len(df) == 0:
        fig = px.scatter_mapbox(geodf,
                                lat=geodf.lat, lon=geodf.lon,
                                hover_name="job_type",
                                hover_data=["date", "drill_type", 'bit_diam', "usda_class", "mod_class"],
                                color_discrete_sequence=['red'],
                                # color='job_type',
                                # size='bit_diam',
                                zoom=3,
                                # height=400,
                                opacity=0
                                )
        fig.update_layout(mapbox_style="open-street-map",
                          margin={"r": 0, "t": 0, "l": 0, "b": 0},
                          plot_bgcolor=colors['background'],
                          paper_bgcolor=colors['background'],
                          font_color=colors['text'],
                          legend=dict(
                              yanchor="top",
                              y=0.99,
                              xanchor="left",
                              x=0.01
                          )
                          )
        container = ['There are no drill runs during the specified time.']
    else:
        try:
            fig = px.scatter_mapbox(df,
                                    lat=df.lat, lon=df.lon,
                                    hover_name="job_type",
                                    hover_data=["date", "drill_type", 'bit_diam', "usda_class", "mod_class"],
                                    color_discrete_sequence=['red'],
                                    # color='job_type',
                                    # size='bit_diam',
                                    zoom=3,
                                    # height=400,
                                    )
            fig.update_layout(mapbox_style="open-street-map",
                              margin={"r": 0, "t": 0, "l": 0, "b": 0},
                              plot_bgcolor=colors['background'],
                              paper_bgcolor=colors['background'],
                              font_color=colors['text'],
                              # legend=dict(
                              #     yanchor="top",
                              #     y=0.99,
                              #     xanchor="left",
                              #     x=0.01
                              # ),
                              # legend=None
                              )
            count = len(df)
            container = [f'Currently showing {count} drill run(s).']

        except KeyError:
            fig = px.scatter_mapbox(geodf,
                                    lat=geodf.lat, lon=geodf.lon,
                                    hover_name="job_type",
                                    hover_data=["date", "drill_type", "usda_class", "mod_class"],
                                    # color_discrete_sequence=[colors['background']],
                                    color='job_type',
                                    size='bit_diam',
                                    zoom=2,
                                    # height=400,
                                    opacity=0
                                    )
            fig.update_layout(mapbox_style="open-street-map",
                              margin={"r": 0, "t": 0, "l": 0, "b": 0},
                              plot_bgcolor=colors['background'],
                              paper_bgcolor=colors['background'],
                              font_color=colors['text'],
                              legend=dict(
                                  yanchor="top",
                                  y=0.99,
                                  xanchor="left",
                                  x=0.01
                              )
                              )
            container = ['There are no drill runs during the specified time.']
    return container, fig


if __name__ == '__main__':
    app.run_server(debug=True)
