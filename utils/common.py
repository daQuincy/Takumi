from sklearn.metrics import confusion_matrix

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import json
import pytz

def read_bm_data(file_path):
    df_wti = pd.read_csv(
        file_path,
        sep=';', header=0,
        names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'],
        engine='c'
    )

    df_wti['date'] = pd.to_datetime(df_wti['date'], format='%d/%m/%Y')
    df_wti['date'] = df_wti['date'].dt.strftime('%m-%d-%Y')

    df_wti['datetime'] = pd.to_datetime(df_wti['date'] + ' ' + df_wti['time'])

    df_wti['datetime'] = df_wti['datetime'].dt.tz_localize('Etc/GMT+6')
    ny_tz = pytz.timezone('America/New_York')
    df_wti['datetime'] = df_wti['datetime'].dt.tz_convert(ny_tz)
    df_wti['datetime'] = pd.to_datetime(df_wti['datetime'])
    df_wti['date'] = df_wti['datetime'].dt.strftime('%Y-%m-%d')
    df_wti['time'] = df_wti['datetime'].dt.strftime('%H%M')
    df_wti['day'] = df_wti['datetime'].dt.strftime('%A')

    return df_wti

def plot_confusion_matrix(y_true, y_pred, class_names, title='Confusion Matrix', cmap=plt.cm.Blues, normalize=False):
    """
    Plots a confusion matrix with clear visualization.

    Args:
        cm (np.ndarray): The confusion matrix to plot.
        class_names (list): A list of class names for the matrix.
        title (str, optional): Title for the plot. Defaults to 'Confusion Matrix'.
        cmap (matplotlib colormap, optional): Colormap for the matrix. Defaults to plt.cm.Blues.
    """

    if normalize:
        cm = confusion_matrix(y_true, y_pred, normalize='pred')
    else:
        cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(4, 4))  # Set appropriate figure size

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45, ha='right')
    plt.yticks(tick_marks, class_names)

    # Normalize for better visualization
    # cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    thresh = cm.max() / 2.
    for i, j in np.ndindex(cm.shape):
        plt.text(j, i, f"{cm[i, j]:.2f}", ha="center", va="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()

def create_correlation_heatmap(df):
    correlations = df.corr()
    sns.heatmap(correlations, annot=True, cmap='coolwarm')
    plt.show()

def print_json(data):
    data = json.dumps(data, indent=2)
    print(data)

def print_dictionary_tree(dictionary, indent=0):
    for key, value in dictionary.items():
        print(f"{'  ' * indent}{key}:")
        if isinstance(value, dict):
            print_dictionary_tree(value, indent + 1)
            print()
        else:
            print(f"{'  ' * (indent + 1)}{value}")