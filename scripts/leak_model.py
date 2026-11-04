"""Shared ML helpers: input features, the averaging ensemble, and the saved-model wrapper.

Part B and Part C use TransistorModel to predict terminal currents:

    from leak_model import TransistorModel
    m = TransistorModel.load("saved_models/nmos_off.joblib")
    currents = m.predict(df)   # df columns: vdd, temp, w, vd, vs, vg, vb, vth0, toxe, ndep, u0, xj
    # returns a DataFrame with id, ig, is, ib (A, current INTO each terminal)

How a current is predicted:
    magnitude: a regressor predicts log10(|I|)
    sign:      a classifier predicts + or - (or a constant, if the sign never changes)
    I = sign * 10 ** log10(|I|)
"""
import joblib
import numpy as np
import pandas as pd

TARGETS = ["id", "ig", "is", "ib"]
RAW_INPUTS = ["vdd", "temp", "w", "vd", "vs", "vg", "vb",
              "vth0", "toxe", "ndep", "u0", "xj"]
LOG_FLOOR = 1e-30          # avoids log10(0) for currents that are exactly zero


def to_log(i):
    return np.log10(np.abs(np.asarray(i, dtype=float)) + LOG_FLOOR)


def make_features(df, dev_type):
    """Raw inputs plus terminal-voltage features that set the device physics.

    Voltages are flipped for PMOS (s = -1) so that 'positive' means 'turning on'
    for both device types.
    """
    s = 1.0 if dev_type == "nmos" else -1.0
    X = pd.DataFrame(index=df.index)
    X["vdd"] = df["vdd"]
    X["temp"] = df["temp"]
    X["log_w"] = np.log(df["w"])
    X["vd"] = df["vd"]
    X["vs"] = df["vs"]
    X["vth0"] = df["vth0"]
    X["toxe_nm"] = df["toxe"] * 1e9
    X["ndep"] = df["ndep"] / 1e18
    X["u0"] = df["u0"]
    X["xj_nm"] = df["xj"] * 1e9
    X["vds"] = df["vd"] - df["vs"]
    X["log_abs_vds"] = np.log10(np.abs(df["vd"] - df["vs"]) + 1e-6)
    X["vgs"] = s * (df["vg"] - df["vs"])
    X["vgd"] = s * (df["vg"] - df["vd"])
    X["vbs"] = s * (df["vb"] - df["vs"])
    X["vbd"] = s * (df["vb"] - df["vd"])
    X["inv_t"] = 1.0 / (df["temp"] + 273.15)
    X["vgs_per_tox"] = X["vgs"] / X["toxe_nm"]       # oxide field -> gate tunnelling
    X["vgd_per_tox"] = X["vgd"] / X["toxe_nm"]
    return X


class AvgEnsemble:
    """Average of several regressors trained with different random seeds."""

    def __init__(self, models):
        self.models = models

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.models], axis=0)


class SignModel:
    """Predicts +1 / -1. Constant if the training data never changes sign."""

    def __init__(self, y_train, classifier_factory, X_train):
        pos = (np.asarray(y_train) > 0).astype(int)
        if pos.min() == pos.max():
            self.constant = 1.0 if pos[0] == 1 else -1.0
            self.clf = None
        else:
            self.constant = None
            self.clf = classifier_factory().fit(X_train, pos)

    def predict(self, X):
        if self.clf is None:
            return np.full(len(X), self.constant)
        return np.where(self.clf.predict(X) == 1, 1.0, -1.0)


class TransistorModel:
    """Magnitude regressor + sign model for each terminal current of one case."""

    def __init__(self, case, dev_type, model_type, magnitude, sign, feature_names):
        self.case = case
        self.dev_type = dev_type
        self.model_type = model_type
        self.magnitude = magnitude          # {"id": regressor, ...}
        self.sign = sign                    # {"id": SignModel, ...}
        self.feature_names = feature_names

    def features(self, df):
        return make_features(df, self.dev_type)[self.feature_names]

    def predict(self, df):
        X = self.features(df)
        out = pd.DataFrame(index=df.index)
        for t in TARGETS:
            out[t] = self.sign[t].predict(X) * 10.0 ** self.magnitude[t].predict(X)
        return out

    def save(self, path):
        joblib.dump(self, path, compress=3)

    @staticmethod
    def load(path):
        return joblib.load(path)
