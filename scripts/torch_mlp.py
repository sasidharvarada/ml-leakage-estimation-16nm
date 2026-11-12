"""PyTorch MLP regressor with a scikit-learn style fit / predict (uses the GPU if present).

Training: inputs and target are standardised, then
    1. Adam on the full training set with a cosine learning-rate schedule
    2. L-BFGS polishing on the full training set (very effective for smooth targets)
The trained weights are stored on the CPU, so a saved model can be loaded and
used on any machine (with or without a GPU).
"""
import numpy as np

try:
    import torch
    from torch import nn
    TORCH_OK = True
except ImportError:          # the rest of the project still works without torch
    TORCH_OK = False


def device():
    return "cuda" if TORCH_OK and torch.cuda.is_available() else "cpu"


def _net(n_in, hidden):
    layers, prev = [], n_in
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.SiLU()]
        prev = h
    layers.append(nn.Linear(prev, 1))
    return nn.Sequential(*layers)


class TorchMLPRegressor:
    def __init__(self, hidden=(128, 128, 64), adam_steps=3000, lr=3e-3,
                 lbfgs_iters=20000, seed=0, verbose=False):
        self.hidden = tuple(hidden)
        self.adam_steps = adam_steps
        self.lr = lr
        self.lbfgs_iters = lbfgs_iters
        self.seed = seed
        self.verbose = verbose

    def fit(self, X, y):
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        dev = device()
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).reshape(-1)
        self.x_mean, self.x_std = X.mean(0), X.std(0) + 1e-12
        self.y_mean, self.y_std = y.mean(), y.std() + 1e-12
        Xt = torch.tensor((X - self.x_mean) / self.x_std, dtype=torch.float32, device=dev)
        yt = torch.tensor((y - self.y_mean) / self.y_std, dtype=torch.float32, device=dev).view(-1, 1)

        net = _net(X.shape[1], self.hidden).to(dev)
        loss_fn = nn.MSELoss()

        opt = torch.optim.Adam(net.parameters(), lr=self.lr)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=self.adam_steps, eta_min=self.lr * 1e-3)
        for step in range(self.adam_steps):
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(net(Xt), yt)
            loss.backward()
            opt.step()
            sched.step()
            if self.verbose and step % 1000 == 0:
                print(f"    adam {step:5d}  mse {loss.item():.3e}")

        if self.lbfgs_iters > 0:
            lb = torch.optim.LBFGS(net.parameters(), lr=1.0, max_iter=self.lbfgs_iters,
                                   history_size=50, tolerance_grad=1e-12, tolerance_change=1e-15,
                                   line_search_fn="strong_wolfe")

            def closure():
                lb.zero_grad(set_to_none=True)
                l = loss_fn(net(Xt), yt)
                l.backward()
                return l
            lb.step(closure)
            if self.verbose:
                print(f"    lbfgs done  mse {loss_fn(net(Xt), yt).item():.3e}")

        self.state = {k: v.detach().cpu() for k, v in net.state_dict().items()}
        self.n_in = X.shape[1]
        self._net = None
        return self

    def _cpu_net(self):
        if getattr(self, "_net", None) is None:
            net = _net(self.n_in, self.hidden)
            net.load_state_dict(self.state)
            net.eval()
            self._net = net
        return self._net

    def predict(self, X):
        X = np.asarray(X, dtype=np.float64)
        xs = torch.tensor((X - self.x_mean) / self.x_std, dtype=torch.float32)
        with torch.no_grad():
            out = self._cpu_net()(xs).numpy().reshape(-1)
        return out * self.y_std + self.y_mean

    def __getstate__(self):
        d = self.__dict__.copy()
        d["_net"] = None
        return d
