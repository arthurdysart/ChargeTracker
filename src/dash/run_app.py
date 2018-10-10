"""
Display errors in realtime from simulated server lab tests
Graph displays percent of servers impacted per (SW,HW) config on x axis
Graph displays percent of tests with errors per (SW,HW) config on the y axis
Hover over each marker to get error counts and number of servers impacted 
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
app = dash.Dash("Charge_Tracker")
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
    output = cass_db.execute(query, timeout=None)
    results = output._current_rows
    return results

# Callback updates graph (OUTPUT) according to time interval (INPUT)
@app.callback(Output('capacity_tracker','figure'),
              [Input('real_time_updates', 'n_intervals')])
def update_summary_graph(interval):
    """
    Queries table, analyzes data, and assembles results in proper Dash format. 
    """
    # Pulls all data from Cassandra
    df_capacity = query_cassandra("""
                                  SELECT step, id, cathode, cycle,
                                  double_sum(capacity) AS sum_capacity
                                  FROM X WHERE step = 'D';
                                  """)

    print(df_capacity)
    # Analyzes dataframe to report average results

    # Retrieves x and y data to be plotted on graph
    x = df_capacity["cycle"]
    y = df_capacity["sum_capacity"]

    # Creates mouseover text (index corresponds to index of x and y datasets)
    all_cathode = df_capacity["cathode"].tolist()
    all_step = df_capacity["step"].tolist()
    all_id = df_capacity["id"].tolist()
    metadata = zip(all_id, all_cathode, all_step)
    mouseover_text = ["Battery ID: {}\nCathode: {}\nStep: {}".format(bid, cathode, step) for bid, cathode, step in metadata]

    # Assembles data (X and Y data as lists) and layout parameters for Dash
    data=[{"x": x,
           "y": y,
           "mode": "markers",
           "text": mouseover_text},]
    layout={"height": 500, \
            "xaxis": {"title": "Cycle number"}, \
            "yaxis": {"title": "Measured capacity  (mAh)"},}

    return Figure(data=data, layout=layout)


## MAIN MODULE
if __name__ == "__main__":
    # Sets formatting for retrieved database query
    cass_db.row_factory = create_dataframe
    cass_db.default_fetch_size = None

    # Starts Flask/Dash app
    app.run_server(debug=True, host="0.0.0.0", port=80)


## END OF FILE