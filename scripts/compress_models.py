import os
import joblib
import torch
import torch.nn as nn
import numpy as np

# 1. Provide class definitions so pickle can resolve '__main__.ClassName'
class LeakageResNet(nn.Module):
    def __init__(self, in_dim=18, out_dim=4, hidden=128):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden)
        self.act1 = nn.SiLU()
        self.fc2 = nn.Linear(hidden, hidden)
        self.act2 = nn.SiLU()
        self.fc3 = nn.Linear(hidden, 64)
        self.act3 = nn.SiLU()
        self.out = nn.Linear(64, out_dim)

    def forward(self, x):
        h1 = self.act1(self.fc1(x))
        h2 = self.act2(self.fc2(h1)) + h1
        h3 = self.act3(self.fc3(h2))
        return self.out(h3)

class PyTorchWrapper:
    def __init__(self, model):
        self.model = model
    def predict(self, X):
        self.model.eval()
        with torch.no_grad():
            return self.model(torch.tensor(X, dtype=torch.float32)).cpu().numpy()

class MultiOutputModel:
    def __init__(self, models):
        self.models = models
    def predict(self, X):
        return np.column_stack([m.predict(X) for m in self.models])

# 2. Re-save with compression
def main():
    print("\n")
    print(" compressing saved model packages")
    print("\n")
    for fname in sorted(os.listdir("models")):
        if fname.endswith(".joblib"):
            path = os.path.join("models", fname)
            orig_mb = os.path.getsize(path) / (1024 * 1024)
            
            data = joblib.load(path)
            joblib.dump(data, path, compress=3)
            
            new_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"{fname:22s}: {orig_mb:6.2f} MB  -->  {new_mb:5.2f} MB")
    print("\n")
    print("All models successfully compressed!")

if __name__ == "__main__":
    main()
