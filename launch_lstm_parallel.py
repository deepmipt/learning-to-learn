import re
from environment import Environment
# from gru_par import Gru, BatchGenerator
from lstm_sample_par import Lstm, LstmBatchGenerator
from some_useful_functions import create_vocabulary, get_positions_in_vocabulary

f = open('datasets/scipop_v3.0/scipop_train.txt', 'r', encoding='utf-8')
train_text = re.sub('<[^>]*>', '', f.read( ))
f.close()

f = open('datasets/scipop_v3.0/scipop_valid.txt', 'r', encoding='utf-8')
valid_text = re.sub('<[^>]*>', '', ''.join(f.readlines()[:10]))
f.close()


vocabulary = create_vocabulary(train_text + valid_text)
vocabulary_size = len(vocabulary)

env = Environment(Lstm, LstmBatchGenerator, vocabulary=vocabulary)

# env = Environment(Gru, BatchGenerator)
cpiv = get_positions_in_vocabulary(vocabulary)

connection_interval = 8
connection_visibility = 5
subsequence_length_in_intervals = 10


add_feed = [{'placeholder': 'dropout', 'value': 0.9},
            {'placeholder': 'sampling_prob',
             'value': {'type': 'linear', 'start': 0., 'end': 1., 'interval': 3000}},
            {'placeholder': 'loss_comp_prob',
             'value': {'type': 'linear', 'start': 1., 'end': 0., 'interval': 3000}}]
valid_add_feed = [# {'placeholder': 'sampling_prob', 'value': 1.},
                  {'placeholder': 'dropout', 'value': 1.}]


env.build(batch_size=64,
          num_layers=2,
          num_nodes=[400, 400],
          num_output_layers=2,
          num_output_nodes=[650],
          vocabulary_size=vocabulary_size,
          embedding_size=150,
          num_unrollings=50,
          init_parameter=3.,
          character_positions_in_vocabulary=cpiv,
          num_gpus=2)

env.train(save_path='lstm_sample_test/scipop3_1000_bs256_11.12',
          learning_rate={'type': 'exponential_decay',
                         'init': .002,
                         'decay': .5,
                         'period': 40000},
          batch_size=64,
          num_unrollings=50,
          vocabulary=vocabulary,
          checkpoint_steps=2000,
          result_types=['perplexity', 'loss', 'bpc', 'accuracy'],
          printed_result_types=['perplexity', 'loss', 'bpc', 'accuracy'],
          stop=400000,
          train_dataset_text=train_text,
          validation_dataset_texts=[valid_text],
          results_collect_interval=100,
          additions_to_feed_dict=add_feed,
          validation_additions_to_feed_dict=valid_add_feed)
          #log_device_placement=True)
