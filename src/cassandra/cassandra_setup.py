from cassandra.cluster import Cluster
from ipsettings import casscluster

cluster = Cluster(casscluster())
session = cluster.connect('battery_data')
session.execute("DROP TABLE IF EXISTS energy;")
session.execute("CREATE TABLE IF NOT EXISTS energy(id int, cathode text, cycle int, step text, energy float, PRIMARY KEY(id, cathode, cycle, step)) WITH CLUSTERING ORDER BY (cathode DESC, cycle DESC);")

session.execute("DROP TABLE IF EXISTS power;")
session.execute("CREATE TABLE IF NOT EXISTS power(id int, cathode text, cycle int, step text, power float, PRIMARY KEY(id, cathode, cycle, step)) WITH CLUSTERING ORDER BY (cathode DESC, cycle DESC);")