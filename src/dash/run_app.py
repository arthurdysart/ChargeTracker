"""
Displays summary visual showing aggreagated battery data.
Template:
sudo python run_app.py
"""

# IMPORTED LIBRARIES
from dash.dependencies import Input
from dash.dependencies import Output
from plotly.graph_objs import Figure
from cassandra.cluster import Cluster

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd


# Sets cassandra database and Flask app as global variables
cass_db = Cluster(["10.0.0.74"]).connect("battery_data")
app = dash.Dash("Charge_Tracker",
                external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])
server = app.server
app.layout = html.Div([html.Div([dcc.Graph(id="capacity_tracker"),],
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

# Callback updates graph (OUTPUT) according to time interval (INPUT)
@app.callback(Output('capacity_tracker','figure'),
              [Input('real_time_updates', 'n_intervals')])
def update_summary_graph(interval):
    """
    Queries table, analyzes data, and assembles results in proper Dash format. 
    """
    # Pulls all data from Cassandra into Pandas dataframe
    # TODO: Fix table schema?
    df_capacity = query_cassandra("""
                                  SELECT step, id, cathode, cycle,
                                  double_sum(capacity) AS sum_capacity
                                  FROM battery_data WHERE step = 'D'
                                  ALLOW FILTERING;
                                  """)

    # Analyzes dataframe to report average results
    grouped_data = df_capacity.groupby(["cathode", "cycle", "step"])
    df_capacity_mean = pd.DataFrame({'capacity_mean' : grouped_data["sum_capacity"].mean()}).reset_index()
    df_capacity_stdev = pd.DataFrame({'capacity_stdev' : grouped_data["sum_capacity"].std()}).reset_index()
    df_capacity_count = pd.DataFrame({'capacity_count' : grouped_data["sum_capacity"].count()}).reset_index()

    # Concatenates all calculated values according to 
    # SCHEMA: <cathode>, <cycle>, <capacity-mean>, <capacity-stdev>, <capacity-count>
    mean_stdev = pd.merge(df_capacity_mean, df_capacity_stdev, on=["cathode", "cycle"], how="inner")
    mean_stdev_counts = pd.merge(mean_stdev, df_capacity_count, on=["cathode", "cycle"], how="inner")

    # Retrieves x and y data to be plotted on graph
    x_cycles = mean_stdev_counts["cycle"].tolist()
    y_mean = mean_stdev_counts["capacity_mean"].tolist()
    y_error = mean_stdev_counts["capacity_stdev"].tolist()
    y_percent_error = (mean_stdev_counts["capacity_stdev"] / mean_stdev_counts["capacity_mean"]).tolist()

    # Creates mouseover text (index corresponds to index of x and y datasets)
    text_steps = mean_stdev_counts["step"].tolist()
    text_cathodes = mean_stdev_counts["cathode"].tolist()
    text_counts = mean_stdev_counts["capacity_count"].tolist()
    metadata = zip(text_cathodes,
                   text_counts,
                   text_steps,
                   y_mean,
                   y_percent_error)
    mouseover_text = ["""Chemistry:{}   \
                        Batteries:{}   \
                        Step:{}   \
                        Average:{} Ah +/- {} %   \
                        """.format(*t) for t in metadata]

    # Assembles data (X and Y data as lists) and layout parameters for Dash
    data=[{"x": x_cycles,
           "y": y_mean,
           "mode": "markers",
           "text": mouseover_text,
           "error_y": {"type": "data",
                       "array": y_error,
                       "visible": True,},},]
    layout={"height": 500,
            "xaxis": {"title": "Number of discharges"},
            "yaxis": {"title": "Measured capacity  (Ah)"},}

    return Figure(data=data, layout=layout)


## MAIN MODULE
if __name__ == "__main__":
    # Sets formatting for retrieved database query
    cass_db.row_factory = create_dataframe
    cass_db.default_fetch_size = None

    # Starts Flask/Dash app
    app.run_server(debug=True, host="0.0.0.0", port=80)


## END OF FILE