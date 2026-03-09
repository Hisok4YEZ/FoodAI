import matplotlib.pyplot as plt
from torchvision import datasets, transforms

transform = transforms.Compose([
    transforms.ToTensor()
])

train_ds = datasets.MNIST(root="data", train=True, download=True, transform=transform)

print("Train size:", len(train_ds))
img, label = train_ds[0]
print("One sample shape:", img.shape, "label:", label)

# Affiche une image
plt.imshow(img.squeeze(0), cmap="gray")
plt.title(f"MNIST sample - label={label}")
plt.axis("off")
plt.show()
