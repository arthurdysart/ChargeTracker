"""
Displays summary visual showing aggreagated battery data using Dash library.
Graph 

Template:
sudo python run_app_newschema.py
"""

# IMPORTED LIBRARIES
from dash.dependencies import Input
from dash.dependencies import Output
from cassandra.cluster import Cluster
from itertools import chain as flat

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dte
import pandas as pd
import plotly.graph_objs as go

## GLOBAL DEFINITIONS 
# Sets Cassandra database parameters
db_session = Cluster(["10.0.0.74"]).connect()

# Sets dropdown options
groups = ["W", "X", "Y", "Z"]
cycles = [str(x) for x in range(1000)]
table_order = ["id", "cathode", "cycle", "energy", "percent deviation"]

# Sets Dash application parameters
app = dash.Dash("Charge_Tracker",
                external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])
server = app.server
app.layout = html.Div([
        html.Div([
                dcc.Graph(
                        id="capacity_tracker",
                        figure="figure"),
                dcc.Interval(
                        id="real_time_updates",
                        interval=10000,
                        n_intervals=0)],
                style={
                        "width": "100%",
                        "height": "auto",
                        "display": "scatter"}
                ),
        html.Div([
                html.Div(
                        dcc.Dropdown(
                            id="table_groups",
                            options=[{"label": x, "value": x} for x in groups],
                            placeholder="Select battery group",
                            value="W"),
                        style={
                                "width": "48%",
                                "display": "inline-block"}
                        ),
                html.Div(
                        dcc.Dropdown(
                            id="table_cycles",
                            options=[{"label": x, "value": x} for x in cycles],
                            placeholder="Select cycle",
                            value="0"),
                        style={
                                "width": "48%",
                                "float": "right",
                                "display": "inline-block"}
                        ),
                dte.DataTable(
                        rows=[{}],
                        columns = table_order,
                        id="group_detail")]
                )
        ],
        style={
                "width": "90%",
                "height": "auto",
                "align": "center"}
        )

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
    return db_session.execute(query, timeout=None)._current_rows

def analyze_all_groups():
    """
    Aggregates queried Cassandra data by mean, std dev, counts, and error.
    """
    # Pulls all data from Cassandra into Pandas dataframe
    df_all = query_cassandra("""
                             SELECT
                             cathode,
                             cycle,
                             double_sum(value) AS metric
                             FROM battery_metrics.discharge_energy;
                             """)

    # Calculates aggreates (mean, std dev, count, error, upper/lower limits)
    pg = df_all.groupby(["cathode", "cycle"])
    df = pd.DataFrame({"mean": pg["metric"].mean(),
                       "stdev": pg["metric"].std(),
                       "count": pg["metric"].count(),}).reset_index()
    df["error"] = df["stdev"] * 100.0 / df["mean"]
    return df

def make_trace(df, c, colors):
    """
    For selected cathode "c", creates Plotly scatter objects.
    """
    df_sub = df[df.cathode == c]
    x = df_sub["cycle"].tolist()
    y = df_sub["mean"].tolist()
    y_hi = (df_sub["mean"] + df_sub["stdev"]).tolist()
    y_lo = (df_sub["mean"] - df_sub["stdev"]).tolist()

    metadata = zip(df_sub["mean"].tolist(),
                   df_sub["error"].tolist(),
                   df_sub["cathode"].tolist(),
                   df_sub["count"].tolist(),
                   df_sub["cycle"].tolist(),)
    mouseover_text = ["Average: {:.3f} Ah &#177; {:.1f} %<br>"
                      "Chemistry: {}<br>"
                      "Batteries: {}<br>"
                      "Cycle: {} discharge<br>"\
                      .format(*t) for t in metadata]

    data_val = go.Scatter(x = x,
                          y = y,
                          hoverinfo = "text",
                          legendgroup = "Material {}".format(c),
                          line = {"color": colors[c][0]},
                          mode = "lines+markers",
                          name = "Material {}".format(c),
                          text = mouseover_text,)

    data_err = go.Scatter(x = x + x[::-1],
                          y = y_hi + y_lo[::-1],
                          fill = "tozerox",
                          fillcolor = colors[c][1],
                          hoverinfo = "none",
                          legendgroup = "Material {}".format(c),
                          line = {"color": "rgba(255,255,255,0)"},
                          showlegend = False,
                          name = "Material {}".format(c),)

    return data_val, data_err


# Callback updates graph (OUTPUT) according to time interval (INPUT)
@app.callback(Output("capacity_tracker", "figure"),
              [Input("real_time_updates", "n_intervals")])
def update_graph(interval):
    """
    Queries table, analyzes data, and assembles results in Dash format.
    """
    df = analyze_all_groups()

    # Initializes color schemes and gets all cathode names
    colors = {"W": ("rgb(230,41,55)", "rgba(230,41,55,0.1)"),
              "X": ("rgb(255,117,37)", "rgba(255,117,37,0.1)"),
              "Y": ("rgb(0,169,255)", "rgba(0,169,255,0.1)"),
              "Z": ("rgb(135,60,190)", "rgba(135,60,190,0.1)"),}
    cathodes = df.cathode.unique()

    # Creates all scatter data for real-time graph
    data = [make_trace(df, c, colors) for c in cathodes]
    data = list(flat.from_iterable(data))

    # Sets layout 
    layout = go.Layout(hovermode = "closest",
                       legend = {"orientation": "h"},
                       margin = {"l": 40, "b": 40, "t": 10, "r": 10},
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
                       yaxis = {"title": "Calculated energy  (Wh)",
                                "gridcolor": "rgb(255,255,255)",
                                "showgrid": True,
                                "showline": False,
                                "showticklabels": True,
                                "tickcolor": "rgb(127,127,127)",
                                "ticks": "outside",
                                "zeroline": False},)

    return go.Figure(data = data, layout = layout)

# Callback updates graph (OUTPUT) according to time interval (INPUT)
@app.callback(Output('group_detail', 'rows'),
              [Input('table_groups', 'value'),
               Input('table_cycles', 'value')])
def update_table(group_name, cycle_number, max_rows=50):
    """
    Queries table, analyzes data, and assembles results in Dash format.
    """
    # Pulls all data from Cassandra into Pandas dataframe
    df = query_cassandra("""
                         SELECT
                         id AS id,
                         cathode AS cathode,
                         cycle AS cycle,
                         double_sum(value) AS energy
                         FROM battery_metrics.discharge_energy
                         WHERE cathode=\'{}\' AND cycle={};
                         """.format(group_name, cycle_number))

    print(df)

    # Calculates aggreates (mean, std dev, and percent deviation)
    mean = df["energy"].mean()
    stdev = df["energy"].std()
    df["percent deviation"] = abs(df["energy"] - mean) * 100.0 / (2.0 * stdev)
    df.sort_values(by="percent deviation", ascending=False)

    for n in ("energy", "percent deviation"):
        df[n] = df[n].map(lambda x: '{0:.1f}'.format(x))

    return df.to_dict("records")


## MAIN MODULE
if __name__ == "__main__":
    # Sets formatting for retrieved database query
    db_session.row_factory = create_dataframe
    db_session.default_fetch_size = None

    # Starts Flask/Dash app
    app.run_server(debug=True, host="0.0.0.0", port=80)


## END OF FILE