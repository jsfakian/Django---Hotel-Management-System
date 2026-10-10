import matplotlib.pyplot as plt
import networkx as nx

# Δημιουργία γραφήματος
G = nx.DiGraph()

# Κόμβοι (Υποσυστήματα)
subsystems = [
    "User Management", "Property Management", "Room Management",
    "Guest Management", "Employee Management", "Room Services",
    "Booking Management", "Contract Management", "Pricing Engine (AI)",
    "Payments & Invoices", "Notifications & Communication", "External APIs"
]

# Προσθήκη κόμβων
G.add_nodes_from(subsystems)

# Συνδέσεις μεταξύ των λειτουργιών
edges = [
    ("User Management", "Booking Management"),
    ("User Management", "Payments & Invoices"),
    ("Property Management", "Room Management"),
    ("Property Management", "Booking Management"),
    ("Room Management", "Booking Management"),
    ("Guest Management", "Booking Management"),
    ("Employee Management", "Room Services"),
    ("Room Services", "Booking Management"),
    ("Booking Management", "Contract Management"),
    ("Booking Management", "Pricing Engine (AI)"),
    ("Contract Management", "Pricing Engine (AI)"),
    ("Booking Management", "Payments & Invoices"),
    ("Payments & Invoices", "External APIs"),
    ("Notifications & Communication", "Booking Management"),
    ("Notifications & Communication", "Payments & Invoices"),
    ("External APIs", "Booking Management"),
    ("External APIs", "Contract Management")
]

# Προσθήκη συνδέσεων
G.add_edges_from(edges)

# Σχεδίαση γραφήματος
plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=42)  # Διάταξη των κόμβων
nx.draw(G, pos, with_labels=True, node_size=3500, node_color="lightblue", edge_color="gray", font_size=9, font_weight="bold", arrows=True)
plt.title("Σχεσιακό Διάγραμμα Λειτουργιών του Συστήματος", fontsize=14)

# Αποθήκευση του διαγράμματος
plt.savefig("system_architecture.png", format="png")
plt.show()

