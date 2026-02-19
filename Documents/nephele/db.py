import matplotlib.pyplot as plt
import networkx as nx

# Δημιουργία γραφήματος
G = nx.DiGraph()

# Οντότητες της βάσης δεδομένων
entities = [
    "Users", "Guests", "Properties", "Rooms", "Room Services",
    "Bookings", "Invoices", "Payments", "Employees",
    "Notifications", "Contracts"
]

# Προσθήκη κόμβων (οντοτήτων)
G.add_nodes_from(entities)

# Σχέσεις μεταξύ των οντοτήτων
edges = [
    ("Users", "Bookings"), ("Users", "Payments"), ("Users", "Contracts"),
    ("Guests", "Bookings"), ("Properties", "Rooms"), ("Properties", "Bookings"),
    ("Rooms", "Bookings"), ("Rooms", "Room Services"), ("Bookings", "Invoices"),
    ("Bookings", "Payments"), ("Bookings", "Contracts"), ("Payments", "Invoices"),
    ("Employees", "Room Services"), ("Notifications", "Users")
]

# Προσθήκη συνδέσεων (ξένων κλειδιών)
G.add_edges_from(edges)

# Σχεδίαση γραφήματος
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)  # Διάταξη των κόμβων
nx.draw(G, pos, with_labels=True, node_size=3500, node_color="lightblue", edge_color="gray", font_size=9, font_weight="bold", arrows=True)
plt.title("Διάγραμμα Οντοτήτων Βάσης Δεδομένων", fontsize=14)

# Αποθήκευση του γραφήματος
plt.savefig("database_schema.png", format="png")
plt.show()

