import torch
import matplotlib.pyplot as plt

# Classe 0
c0 = torch.randn(100, 2) * 0.5 + torch.tensor([-2.0, 0.0])

# Classe 1
c1 = torch.randn(100, 2) * 0.5 + torch.tensor([2.0, 0.0])

X = torch.cat([c0, c1], dim=0)
y = torch.cat([
    torch.zeros(100, dtype=torch.long),
    torch.ones(100, dtype=torch.long)
])

plt.scatter(c0[:,0], c0[:,1], label="Classe 0")
plt.scatter(c1[:,0], c1[:,1], label="Classe 1")
plt.legend()
plt.title("Données 2D")
plt.show()
