import xgboost as xgb
import matplotlib.pyplot as plt

from utils.common import print_json
from typing import List, Tuple, Dict
from sklearn.metrics import accuracy_score, precision_score, \
    recall_score, f1_score, classification_report

class XGBoostClassifier:
    def __init__(self, params: Dict = None, fname: str = None, device: str = 'cpu'):
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
                    'device': device
                }
            else:
                self.params = params

            self.model = None

    def fit(self, train_set: Tuple, val_set: Tuple):
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

        ytr_pred = self.model.predict(Xtr)
        yvl_pred = self.model.predict(Xvl)

        self.training_results = {
            'accuracy': {
                'train': accuracy_score(ytr, ytr_pred), 
                'val': accuracy_score(yvl, yvl_pred)
            },
            'precision': {
                'train': precision_score(ytr, ytr_pred, average='weighted'),
                'val': precision_score(yvl, yvl_pred, average='weighted')
            },
            'recall': {
                'train': recall_score(ytr, ytr_pred, average='weighted'),
                'val': recall_score(yvl, yvl_pred, average='weighted')
            },
            'f1': {
                'train': f1_score(ytr, ytr_pred, average='weighted'),
                'val': f1_score(yvl, yvl_pred, average='weighted')
            }
        }

        self.ytr_pred = ytr_pred
        self.yvl_pred = yvl_pred
   
        print_json(self.training_results)

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

    def eval(self, X, y, target_names=None):
        y_pred = self.model.predict(X)
        self.eval_results = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='weighted'),
            'recall': recall_score(y, y_pred, average='weighted'),
            'f1': f1_score(y, y_pred, average='weighted')
        }
        print_json(self.eval_results)
        print(classification_report(y, y_pred, target_names=target_names))