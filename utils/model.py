import xgboost as xgb
import matplotlib.pyplot as plt
import pandas as pd

from utils.common import print_dictionary_tree
from typing import List, Tuple, Dict, Iterable
from sklearn.metrics import accuracy_score, precision_score, \
    recall_score, f1_score, classification_report
from sklearn.dummy import DummyClassifier
from tabulate import tabulate

class BaseClassifier:
    def __init__(self):
        self.model = None
    
    def eval(self, X, y, target_names=None):
        y_pred = self.model.predict(X)
        eval_results = [
            accuracy_score(y, y_pred),
            precision_score(y, y_pred, average="weighted"),
            recall_score(y, y_pred, average="weighted"),
            f1_score(y, y_pred, average="weighted")
        ]
        print(tabulate(pd.DataFrame(eval_results, index=['accuracy', 'precision', 'recall', 'f1']).round(2), tablefmt='psql'))
        # print(classification_report(y, y_pred, target_names=target_names))

    def fit(self, train_set: Tuple, val_set: Tuple, target_names: Iterable = None):
        Xtr, ytr = train_set
        Xvl, yvl = val_set
        self.model.fit(Xtr, ytr)
        print('Training Results:')
        self.eval(Xtr, ytr, target_names)
        print('\nValidation Results:')
        self.eval(Xvl, yvl, target_names)

class DummyClassifierModel(BaseClassifier):
    def __init__(self):
        super().__init__()
        self.model = DummyClassifier()


class XGBoostClassifier(BaseClassifier):
    def __init__(self, params: Dict = None, fname: str = None, device: str = 'cpu'):
        super().__init__()
        if fname is not None:
            self.model = xgb.XGBClassifier(device=device)
            self.model.load_model(fname)
            self.params = self.model.get_xgb_params()
        else:
            if params is None:
                self.params = {
                    'objective': 'multi:softmax',
                    'random_state': 42,
                    'learning_rate': 0.05,
                    'nthread': -1,
                    'max_depth': 5,
                    'num_class': 3,
                    'early_stopping_rounds': 10,
                    'tree_method': 'hist',
                    'enable_categorical': True,
                    'device': device
                }
            else:
                self.params = params

            self.model = None

    def fit(self, train_set: Tuple, val_set: Tuple, target_names: Iterable = None):
        if self.model is None:
            self.model = xgb.XGBClassifier(**self.params)

        Xtr, ytr = train_set
        Xvl, yvl = val_set

        print(f'Training XGBClassifier with the following params: {self.model.get_xgb_params()}')

        self.model.fit(
            Xtr, 
            ytr, 
            eval_set=[(Xtr, ytr), (Xvl, yvl)], 
            verbose=False
        )

        self.model.set_params(device='cpu')
        print('Training Results:')
        self.eval(Xtr, ytr, target_names)
        print('\nValidation Results:')
        self.eval(Xvl, yvl, target_names)

    def plot_training_curve(self):
        results = self.model.evals_result()

        loss = 'mlogloss' if 'multi' in self.params['objective'] else 'logloss'
        train_logloss = results['validation_0'][loss]
        valid_logloss = results['validation_1'][loss]

        plt.figure(figsize=(5, 4))
        plt.plot(train_logloss, label='Training Logloss', color='blue')
        plt.plot(valid_logloss, label='Validation Logloss', color='red')
        plt.xlabel('Boosting Round')
        plt.ylabel('Logloss')
        plt.title('XGBoost Training and Validation Curves')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_importance(self, figsize: Tuple=(8, 10)):
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        xgb.plot_importance(self.model, importance_type='weight', ax=ax)
        plt.show()

    def save_model(self, fname):
        self.model.save_model(fname)