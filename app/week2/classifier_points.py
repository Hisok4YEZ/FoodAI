import torch
import torch.nn as nn
import torch.optim as optim

# Données
c0 = torch.randn(100, 2) * 0.5 + torch.tensor([-2.0, 0.0])
c1 = torch.randn(100, 2) * 0.5 + torch.tensor([2.0, 0.0])

X = torch.cat([c0, c1], dim=0)
y = torch.cat([
    torch.zeros(100, dtype=torch.long),
    torch.ones(100, dtype=torch.long)
])

# Modèle
model = nn.Sequential(
    nn.Linear(2, 16),
    nn.ReLU(),
    nn.Linear(16, 2)
)

# Loss + optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# Entraînement
for epoch in range(200):
    optimizer.zero_grad()
    outputs = model(X)
    loss = criterion(outputs, y)
    loss.backward()
    optimizer.step()

    if epoch % 20 == 0:
        print(f"Epoch {epoch}, Loss = {loss.item():.4f}")

# Accuracy
with torch.no_grad():
    preds = torch.argmax(model(X), dim=1)
    acc = (preds == y).float().mean()
    print("Accuracy:", acc.item())
