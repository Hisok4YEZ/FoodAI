import torch
import torch.nn as nn
import torch.optim as optim

# XOR dataset
X = torch.tensor([
    [0.0, 0.0],
    [0.0, 1.0],
    [1.0, 0.0],
    [1.0, 1.0],
])

y = torch.tensor([0, 1, 1, 0], dtype=torch.long)

# Petit réseau (avec non-linéarité)
model = nn.Sequential(
    nn.Linear(2, 8),
    nn.ReLU(),
    nn.Linear(8, 2)
)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.05)

for epoch in range(1000):
    optimizer.zero_grad()
    out = model(X)
    loss = criterion(out, y)
    loss.backward()
    optimizer.step()

with torch.no_grad():
    preds = torch.argmax(model(X), dim=1)
    acc = (preds == y).float().mean().item()
print("Preds:", preds.tolist())
print("Accuracy:", acc)
