"""
Displays summary visual showing aggreagated battery data using Dash library.
Graph 

Template:
sudo python run_app.py
"""

# IMPORTED LIBRARIES
from dash.dependencies import Input
from dash.dependencies import Output
from plotly.graph_objs import Figure
from cassandra.cluster import Cluster
from itertools import chain as flat

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

## GLOBAL DEFINITIONS 
# Sets Cassandra database parameters
cass_db = Cluster(["10.0.0.74"]).connect("battery_data")

# Sets Dash application parameters
app = dash.Dash("Charge_Tracker",
                external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])
server = app.server
app.layout = html.Div([html.Div([dcc.Graph(id="capacity_tracker",
                                           figure="figure"),],
                                style={"width": "100%",
                                       "height": "auto",
                                       "display": "scatter"}),
                                dcc.Interval(id="real_time_updates",
                                             interval=10000,
                                             n_intervals=0),],
                        style={"width": "90%",
                               "display": "scatter"})

## FUNCTION DEFINITIONS
def create_dataframe(colnames, rows):
    """
    Returns Cassandra query result as Pandas dataframe.
    """
    return pd.DataFrame(rows, columns=colnames)

def query_cassandra(query):
    """
    Queries Cassandra database according to input CQL statement.
    """
    return cass_db.execute(query, timeout=None)._current_rows

def make_trace(df, c, colors):
    """
    For selected cathode "c", creates plot.ly scatter objects.
    """
    df_sub = df[df.cathode == c]
    x = df_sub["cycle"].tolist()
    y = df_sub["mean"].tolist()
    y_hi = (df_sub["mean"] + df_sub["stdev"]).tolist()
    y_lo = (df_sub["mean"] - df_sub["stdev"]).tolist()

    metadata = zip(df_sub["cathode"].tolist(),
                   df_sub["count"].tolist(),
                   df_sub["cycle"].tolist(),
                   df_sub["step"].tolist(),
                   df_sub["mean"].tolist(),
                   df_sub["error"].tolist(),)
    mouseover_text = ["""Chemistry: {}<br>
                        Batteries: {}<br>
                        Cycle: {} {}<br>
                        Average: {:.3f} Ah +- {:.1f} %<br>
                        """.format(*t) for t in metadata]

    data_val = go.Scatter(x = x,
                          y = y,
                          line = {"color": colors[c][0]},
                          mode = "lines+markers",
                          name = c,
                          text = mouseover_text,)

    data_err = go.Scatter(x = x + x[::-1],
                          y = y_hi + y_lo,
                          fill = "tozerox",
                          fillcolor = colors[c][1],
                          line = {"color": "rgba(255,255,255,0)"},
                          showlegend = False,
                          name = c,)
    return data_val, data_err


# Callback updates graph (OUTPUT) according to time interval (INPUT)
@app.callback(Output("capacity_tracker", "figure"),
              [Input("real_time_updates", "n_intervals")])
def update_capacity_graph(interval):
    """
    Queries table, analyzes data, and assembles results in proper Dash format.
    """
    # Pulls all data from Cassandra into Pandas dataframe
    # TODO: Fix table schema?
    df_all = query_cassandra("""
                             SELECT step, id, cathode, cycle,
                             double_sum(capacity) AS sum_val
                             FROM battery_data WHERE step = 'D'
                             ALLOW FILTERING;
                             """)

    # Calculates aggreates (mean, std dev, count, error, upper/lower limits)
    pg = df_all.groupby(["cathode", "cycle", "step"])
    df = pd.DataFrame({"mean": pg["sum_val"].mean(),
                       "stdev": pg["sum_val"].std(),
                       "count": pg["sum_val"].count(),}).reset_index()
    df["error"] = df["stdev"] * 100.0 / df["mean"]

    # Initializes color schemes and gets all cathode names
    colors = {"W": ("rgb(0,100,80)", "rgba(0,100,80,0.1)"),
              "X": ("rgb(0,100,80)", "rgba(0,100,80,0.1)"),
              "Y": ("rgb(0,176,246)", "rgba(0,176,246,0.2)"),
              "Z": ("rgb(231,107,243)", "rgba(231,107,243,0.2)"),}
    cathodes = df.cathode.unique()

    # Creates all scatter data for real-time graph
    data = [make_trace(df, c, colors) for c in cathodes]
    data = list(flat.from_iterable(data))

    # Sets layout 
    layout = go.Layout(hovermode = "closest",
                       legend = {'x': 0, 'y': 1},
                       margin = {'l': 40, 'b': 40, 't': 10, 'r': 10},
                       #paper_bgcolor = "rgb(255,255,255)",
                       #plot_bgcolor = "rgb(229,229,229)",
                       xaxis = {"title": "Number of discharges",
                                "gridcolor": "rgb(255,255,255)",
                                "showgrid": True,
                                "showline": False,
                                "showticklabels": True,
                                "tickcolor": "rgb(127,127,127)",
                                "ticks": "outside",
                                "zeroline": False},
                       yaxis = {"title": "Measured capacity  (Ah)",
                                "gridcolor": "rgb(255,255,255)",
                                "showgrid": True,
                                "showline": False,
                                "showticklabels": True,
                                "tickcolor": "rgb(127,127,127)",
                                "ticks": "outside",
                                "zeroline": False},)

    return go.Figure(data = data, layout = layout)


## MAIN MODULE
if __name__ == "__main__":
    # Sets formatting for retrieved database query
    cass_db.row_factory = create_dataframe
    cass_db.default_fetch_size = None

    # Starts Flask/Dash app
    app.run_server(debug=True, host="0.0.0.0", port=80)


## END OF FILE