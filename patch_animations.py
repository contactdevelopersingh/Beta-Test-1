import os

files_to_patch = [
    ("frontend/src/pages/MarketsPage.jsx", 'className="glass-panel card-hover', 'className="glass-panel card-hover slide-in-right stagger-1'),
    ("frontend/src/pages/DashboardPage.jsx", 'className="glass-panel"', 'className="glass-panel scale-up stagger-2"'),
]

for filepath, search, replace in files_to_patch:
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            content = f.read()
        content = content.replace(search, replace)
        with open(filepath, "w") as f:
            f.write(content)
