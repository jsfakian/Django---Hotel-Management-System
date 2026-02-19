import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Δημιουργία διαγράμματος ER
fig, ax = plt.subplots(figsize=(15, 10))

# Λίστα με τα πλαίσια (οντότητες) και τα χαρακτηριστικά τους
entities = {
    "Users": ["ID", "Name", "Role", "Email", "Password"],
    "Guests": ["ID", "Name", "Preferences"],
    "Properties": ["ID", "Name", "Location"],
    "Rooms": ["ID", "Type", "Price"],
    "Bookings": ["ID", "UserID", "RoomID", "Dates"],
    "Payments": ["ID", "Amount", "Status"],
    "Contracts": ["ID", "Terms", "Agents"],
    "Notifications": ["ID", "Message"],
}

# Θέσεις για κάθε οντότητα
positions = {
    "Users": (0, 8),
    "Guests": (0, 5),
    "Properties": (5, 8),
    "Rooms": (5, 5),
    "Bookings": (10, 8),
    "Payments": (10, 5),
    "Contracts": (15, 8),
    "Notifications": (15, 5),
}

# Σχεδίαση πλαισίων για κάθε οντότητα
for entity, attrs in entities.items():
    x, y = positions[entity]
    width = 3
    height = 1 + 0.3 * len(attrs)
    ax.add_patch(mpatches.Rectangle((x, y), width, height, edgecolor='black', facecolor='lightblue', lw=2))
    ax.text(x + width / 2, y + height - 0.3, entity, ha='center', va='top', fontsize=10, fontweight='bold')
    for i, attr in enumerate(attrs):
        ax.text(x + 0.1, y + height - 0.6 - i * 0.3, f"- {attr}", fontsize=9, va='top')

# Σχέσεις μεταξύ των οντοτήτων
relations = [
    ("Users", "Bookings"),
    ("Users", "Payments"),
    ("Guests", "Bookings"),
    ("Properties", "Rooms"),
    ("Rooms", "Bookings"),
    ("Bookings", "Payments"),
    ("Bookings", "Contracts"),
    ("Users", "Notifications"),
]

# Σχεδίαση γραμμών σχέσεων
for src, dest in relations:
    x1, y1 = positions[src]
    x2, y2 = positions[dest]
    ax.arrow(x1 + 3, y1 + 0.5, x2 - x1 - 3, y2 - y1, head_width=0.3, head_length=0.3, fc='gray', ec='gray', length_includes_head=True)

# Ρυθμίσεις γραφήματος
ax.set_xlim(-1, 20)
ax.set_ylim(0, 12)
ax.set_aspect('equal', adjustable='datalim')
ax.axis('off')
plt.title("ER-Diagram για το Σύστημα Διαχείρισης Ξενοδοχείων", fontsize=14)

# Εμφάνιση ή αποθήκευση
plt.savefig("er_diagram_hotel_management.png", format="png")
plt.show()

