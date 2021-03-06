import tensorflow as tf
ROOT_HEIGHT = 5
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[ROOT_HEIGHT]
sys.path.append(str(root))
try:
    sys.path.remove(str(parent))
except ValueError:  # Already removed
    pass

from learning_to_learn.environment import Environment
from learning_to_learn.pupils.lstm_for_meta import Lstm, LstmFastBatchGenerator as BatchGenerator
from learning_to_learn.useful_functions import create_vocabulary

from learning_to_learn.optimizers.empty import Empty

import os

conf_file = sys.argv[1]
save_path = os.path.join(conf_file.split('.')[0], 'results')

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

with open(conf_file, 'r') as f:
    lines = f.read().split('\n')

dataset_path = os.path.join(*(['..']*ROOT_HEIGHT + ['datasets', 'text8.txt']))
with open(dataset_path, 'r') as f:
    text = f.read()


valid_size = 10000

valid_text = text[:valid_size]
train_text = text[valid_size:]

vocabulary = create_vocabulary(text)
vocabulary_size = len(vocabulary)
print(vocabulary_size)

env = Environment(
    pupil_class=Lstm,
    meta_optimizer_class=Empty,
    batch_generator_classes=BatchGenerator,
    vocabulary=vocabulary)

add_metrics = ['bpc', 'perplexity', 'accuracy']

BATCH_SIZE = 32
NUM_UNROLLINGS = 10
env.build_pupil(
    batch_size=BATCH_SIZE,
    num_layers=1,
    num_nodes=[100],
    num_output_layers=1,
    num_output_nodes=[],
    vocabulary_size=vocabulary_size,
    embedding_size=150,
    num_unrollings=NUM_UNROLLINGS,
    init_parameter=2.,
    num_gpus=1,
    regime='training_with_meta_optimizer',
    going_to_limit_memory=True,
    additional_metrics=add_metrics,
)

env.build_optimizer(
    regime='inference',
    additional_metrics=add_metrics,
    get_omega_and_beta=True,
    matrix_mod='omega',
)


add_feed = [
    {'placeholder': 'dropout', 'value': .9},
    dict(
        placeholder='learning_rate',
        value=2.
    )
]
valid_add_feed = [
    {'placeholder': 'dropout', 'value': 1.},
]
tf.set_random_seed(1)
env.train(
    # gpu_memory=.3,
    num_unrollings=NUM_UNROLLINGS,
    vocabulary=vocabulary,
    with_meta_optimizer=True,
    allow_growth=True,
    save_path='debug_empty_optimizer',
    batch_size=BATCH_SIZE,
    checkpoint_steps=None,
    result_types=['perplexity', 'loss', 'bpc', 'accuracy'],
    printed_result_types=['perplexity', 'loss', 'bpc', 'accuracy'],
    stop=1000,
    # stop=4000,
    train_dataset_text=train_text,
    validation_dataset_texts=[valid_text],
    results_collect_interval=100,
    additions_to_feed_dict=add_feed,
    validation_additions_to_feed_dict=valid_add_feed,
    no_validation=False,
)
