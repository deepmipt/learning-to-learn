ROOT_HEIGHT = 4
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[ROOT_HEIGHT]
sys.path.append(str(root))
try:
    sys.path.remove(str(parent))
except ValueError: # Already removed
    pass

from learning_to_learn.environment import Environment
from learning_to_learn.pupils.mlp_for_meta import MlpForMeta as Mlp
from learning_to_learn.image_batch_gens import MnistBatchGenerator
from learning_to_learn.useful_functions import create_vocabulary

from learning_to_learn.optimizers.res_net_opt import ResNet4Lstm

import os

conf_file = sys.argv[1]
save_path = os.path.join(conf_file.split('.')[0], 'results')

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

with open(conf_file, 'r') as f:
    lines = f.read().split('\n')
restore_path = lines[0]
pretrain_step = int(lines[1])

data_dir = os.path.join(*(['..']*ROOT_HEIGHT + ['datasets', 'mnist']))

env = Environment(pupil_class=Mlp, batch_generator_classes=MnistBatchGenerator)
env = Environment(
    pupil_class=Lstm,
    meta_optimizer_class=ResNet4Lstm,
    batch_generator_classes=BatchGenerator,
    vocabulary=vocabulary)

add_metrics = ['bpc', 'perplexity', 'accuracy']
NUM_EXERCISES = 10
NUM_UNROLLINGS = 4
tmpl = os.path.join(*['..']*ROOT_HEIGHT + [restore_path, 'checkpoints', '%s'])
RESTORE_PUPIL_PATHS = [
    tmpl % 0
]
OPT_INF_RESTORE_PUPIL_PATHS = [
    ('pretrain%s' % 0, RESTORE_PUPIL_PATHS[0])
]
PUPIL_RESTORE_PATHS = [
    RESTORE_PUPIL_PATHS[0]
]

BATCH_SIZE = 32
env.build_pupil(
    batch_size=BATCH_SIZE,
    num_layers=1,
    num_hidden_nodes=[],
    input_shape=[784],
    num_classes=10,
    init_parameter=3.,
    additional_metrics=add_metrics,
    optimizer='sgd'
)

env.build_optimizer(
    regime='train',
    # regime='inference',
    num_optimizer_unrollings=10,
    num_exercises=NUM_EXERCISES,
    res_size=2000,
    permute=False,
    optimizer_for_opt_type='adam',
    additional_metrics=add_metrics,
    clip_norm=100.,
    optimizer_init_parameter=.1
)


train_opt_add_feed = [
    {'placeholder': 'dropout', 'value': .9},
    {'placeholder': 'optimizer_dropout_keep_prob', 'value': .9}
]
opt_inf_add_feed = [
    {'placeholder': 'dropout', 'value': .9},
    {'placeholder': 'optimizer_dropout_keep_prob', 'value': 1.}
]
valid_add_feed = [
    {'placeholder': 'dropout', 'value': 1.},
    {'placeholder': 'optimizer_dropout_keep_prob', 'value': 1.}
]

env.train_optimizer(
    allow_growth=True,
    save_path=save_path,
    result_types=['loss', 'bpc', 'perplexity', 'accuracy'],
    additions_to_feed_dict=train_opt_add_feed,
    pupil_restore_paths=PUPIL_RESTORE_PATHS,
    # pupil_restore_paths=['debug_empty_meta_optimizer/not_learning_issue_es20_nn20/checkpoints/0'],
    reset_period=1,
    num_exercises=NUM_EXERCISES,
    stop=4000,
    train_dataset_texts=[train_text],
    opt_inf_is_performed=True,
    opt_inf_stop=500,
    opt_inf_pupil_restore_paths=OPT_INF_RESTORE_PUPIL_PATHS,
    opt_inf_additions_to_feed_dict=opt_inf_add_feed,
    opt_inf_validation_dataset_texts=[valid_text],
    opt_inf_train_dataset_texts=[train_text],
    validation_additions_to_feed_dict=valid_add_feed,
    vocabulary=vocabulary,
    batch_size=32,
    batch_gen_init_is_random=False,
    num_unrollings=NUM_UNROLLINGS,
    learning_rate={'type': 'exponential_decay',
                   'init': .001,
                   'decay': .1,
                   'period': 3500},
    results_collect_interval=100,
    opt_inf_results_collect_interval=1,
    permute=False,
    summary=True,
    add_graph_to_summary=True
)