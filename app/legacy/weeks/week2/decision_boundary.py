import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

# -------------------------
# 1) Données 2D
# -------------------------
torch.manual_seed(0)
c0 = torch.randn(100, 2) * 0.5 + torch.tensor([-2.0, 0.0])
c1 = torch.randn(100, 2) * 0.5 + torch.tensor([2.0, 0.0])

X = torch.cat([c0, c1], dim=0)
y = torch.cat([
    torch.zeros(100, dtype=torch.long),
    torch.ones(100, dtype=torch.long)
])

# -------------------------
# 2) Modèle
# -------------------------
model = nn.Sequential(
    nn.Linear(2, 16),
    nn.ReLU(),
    nn.Linear(16, 2)
)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# -------------------------
# 3) Entraînement
# -------------------------
for epoch in range(200):
    optimizer.zero_grad()
    outputs = model(X)
    loss = criterion(outputs, y)
    loss.backward()
    optimizer.step()

# -------------------------
# 4) Accuracy
# -------------------------
with torch.no_grad():
    preds = torch.argmax(model(X), dim=1)
    acc = (preds == y).float().mean().item()
print("Accuracy:", acc)

# -------------------------
# 5) Frontière de décision
# -------------------------
x_min, x_max = X[:, 0].min().item() - 1, X[:, 0].max().item() + 1
y_min, y_max = X[:, 1].min().item() - 1, X[:, 1].max().item() + 1

xx, yy = torch.meshgrid(
    torch.linspace(x_min, x_max, 300),
    torch.linspace(y_min, y_max, 300),
    indexing="ij"
)

grid = torch.stack([xx.reshape(-1), yy.reshape(-1)], dim=1)

with torch.no_grad():
    logits = model(grid)
    Z = torch.argmax(logits, dim=1).reshape(300, 300)

plt.figure()
plt.contourf(xx.numpy(), yy.numpy(), Z.numpy(), alpha=0.3)
plt.scatter(c0[:, 0].numpy(), c0[:, 1].numpy(), label="Classe 0")
plt.scatter(c1[:, 0].numpy(), c1[:, 1].numpy(), label="Classe 1")
plt.legend()
plt.title("Frontière de décision (réseau de neurones)")
plt.show()
