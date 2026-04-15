import torch

# Création de tensors
a = torch.tensor([1.0, 2.0, 3.0])
b = torch.randn(3)
c = torch.zeros((2, 3))

print("a:", a)
print("b:", b)
print("c:", c)

# Opérations
print("a + b:", a + b)
print("a * 2:", a * 2)

# Gradients
x = torch.tensor(2.0, requires_grad=True)
y = x ** 2 + 3 * x + 1
y.backward()

print("y:", y.item())
print("dy/dx:", x.grad)
