import tensorflow as tf
from useful_functions import construct, get_keys_from_nested, get_obj_elem_by_path, write_elem_in_obj_by_path


class Meta(object):

    @staticmethod
    def _stack_different_exercises_variables(variables):
        """stack variables from different checkpoints or permutations.
         Stacking is performed along dimension which is last to tensor inner dimensions
         Args:
             variables - dictionary with _pupil variables.
             Each dictionary value is either a list of lists of variables or a list of variables.
             In the first case inner list is a list of variables across different checkpoints
             and outer listing is made across varibles of similar function, e. g. weights from different layers.
             In the second case list is a list a list of variables across different checkpoints."""
        stacked = dict()
        for k, v in variables.items():
            if isinstance(v[0], list()):
                stacked[k] = list()
                for one_var in v:
                    stacked[k].append(tf.stack(one_var))
            else:
                stacked[k] = tf.stack(v)
        return stacked

    @staticmethod
    def _gpu_idx_borders(gpu_map):
        borders = list()
        start = 0
        for idx, gpu_idx in enumerate(gpu_map):
            if gpu_map[start] != gpu_idx:
                borders.append([start, idx])
                start = idx
        borders.append([start, len(gpu_map)])
        return borders

    @staticmethod
    def _stack_placeholders(gpu_borders, placeholders):
        if isinstance(placeholders[0], list):
            stacked_by_gpus = [list() for _ in range(len(gpu_borders))]
            for gpu_idx, borders in enumerate(gpu_borders):
                with tf.device('/gpu:%s' % gpu_idx):
                    ex_placeholders = placeholders[borders[0]:borders[1]]
                    for unr_pl in zip(*ex_placeholders):
                        stacked_by_gpus[gpu_idx].append(tf.stack(unr_pl))
        else:
            stacked_by_gpus = list()
            for borders in gpu_borders:
                stacked_by_gpus.append(tf.stack(placeholders[borders[0]:borders[1]]))
        return stacked_by_gpus

    @staticmethod
    def _stack_trainable_variables(trainable):
        stacked = construct(trainable[0])
        for ok, ov in stacked.items():
            for ik in ov.keys():
                stacked[ok][ik] = tf.stack([tr[ok][ik] for tr in trainable])
        return stacked

    @staticmethod
    def _stack_storages(storages):
        stacked = construct(storages[0])
        paths = get_keys_from_nested(stacked)
        for path in paths:
            write_elem_in_obj_by_path(
                stacked, path,
                tf.stack(
                    [get_obj_elem_by_path(stor, path) for stor in storages])
            )
        return stacked

    @classmethod
    def _stack_exercises(
            cls,
            gpu_map,
            pupil_grad_eval_inputs,
            pupil_grad_eval_labels,
            optimizer_grad_inputs,
            optimizer_grad_labels,
            pupil_trainable_variables,
            pupil_grad_eval_pupil_storage,
            optimizer_grad_pupil_storage
    ):
        gpu_borders = cls._gpu_idx_borders(gpu_map)
        pupil_grad_eval_inputs = cls._stack_placeholders(gpu_borders, pupil_grad_eval_inputs)
        pupil_grad_eval_labels = cls._stack_placeholders(gpu_borders, pupil_grad_eval_labels)
        optimizer_grad_inputs = cls._stack_placeholders(gpu_borders, optimizer_grad_inputs)
        optimizer_grad_labels = cls._stack_placeholders(gpu_borders, optimizer_grad_labels)
        pupil_trainable_variables = cls._stack_trainable_variables(pupil_trainable_variables)
        pupil_grad_eval_pupil_storage = cls._stack_storages(pupil_grad_eval_pupil_storage)
        optimizer_grad_pupil_storage = cls._stack_storages(optimizer_grad_pupil_storage)
        return pupil_grad_eval_inputs, pupil_grad_eval_labels, optimizer_grad_inputs, optimizer_grad_labels, \
               pupil_trainable_variables, pupil_grad_eval_pupil_storage, optimizer_grad_pupil_storage

    @staticmethod
    def _stack_duplicate_o_s(optimizer_ins):
        """Stacking if one matrix is used several times"""
        stacked = dict()
        stack_keys = ['o', 's']
        for k, v in optimizer_ins.items():
            stacked[k] = construct(v)
            for stack_key in stack_keys:
                one_set = v[stack_key]
                if isinstance(one_set, list):
                    united = tf.stack(one_set)
                    united_ndims = len(united.get_shape().as_list())
                    perm = [1, 0] + [i for i in range(2, united_ndims)]
                    stacked[k][stack_key] = tf.transpose(united, perm=perm)
        return stacked

    @staticmethod
    def _make_inputs_and_labels_placeholders(pupil, num_unrollings, num_exercises, gpu_map):
        """If both num_unrollings is not None outputs are lists of lists where
        inner list is for unrollings and outer is for exercises. If num_unrollings is None outputs are lists of
        placeholders."""
        pupil_grad_eval_inputs = list()
        pupil_grad_eval_labels = list()

        optimizer_grad_inputs = list()
        optimizer_grad_labels = list()

        for ex_idx in range(num_exercises):
            if num_unrollings is not None:
                pupil_grad_eval_inputs.append(list())
                pupil_grad_eval_labels.append(list())
                optimizer_grad_inputs.append(list())
                optimizer_grad_labels.append(list())
            with tf.name_scope('exercise_%s' % ex_idx):
                with tf.name_scope('pupil_grad_eval_placeholders'):
                    if num_unrollings is not None:
                        for i in range(num_unrollings):
                            placeholders = pupil.make_inputs_and_labels_placeholders(
                                '/gpu:%s' % gpu_map[ex_idx], 'unrolling_%s' % i)
                            pupil_grad_eval_inputs[ex_idx].append(placeholders['inputs'])
                            pupil_grad_eval_labels[ex_idx].append(placeholders['labels'])
                    else:
                        placeholders = pupil.make_inputs_and_labels_placeholders(
                            '/gpu:%s' % gpu_map[ex_idx], None)
                        pupil_grad_eval_inputs.append(placeholders['inputs'])
                        pupil_grad_eval_labels.append(placeholders['labels'])
                with tf.name_scope('optimizer_grad_placeholders'):
                    if num_unrollings is not None:
                        for i in range(num_unrollings):
                            placeholders = pupil.make_inputs_and_labels_placeholders(
                                '/gpu:%s' % gpu_map[ex_idx], 'unrolling_%s' % i)
                            optimizer_grad_inputs[ex_idx].append(placeholders['inputs'])
                            optimizer_grad_labels[ex_idx].append(placeholders['labels'])
                    else:
                        placeholders = pupil.make_inputs_and_labels_placeholders(
                            '/gpu:%s' % gpu_map[ex_idx], None)
                        optimizer_grad_inputs.append(placeholders['inputs'])
                        optimizer_grad_inputs.append(placeholders['labels'])
        return pupil_grad_eval_inputs, pupil_grad_eval_labels, optimizer_grad_inputs, optimizer_grad_labels

    @staticmethod
    def _create_pupil_variables_and_savers(pupil, num_exercises, gpu_map):
        trainable = list()
        pupil_grad_eval_pupil_storage = list()
        optimizer_grad_pupil_storage = list()
        savers = list()
        for ex_idx in range(num_exercises):
            tr = pupil.create_trainable_variables_dictionary_for_optimizer(
                gpu_map[ex_idx], 'trainable_vars_ex_%s' % ex_idx)
            savers.append(pupil.create_saver(tr))
            trainable.append(tr)
            pupil_grad_eval_pupil_storage.append(pupil.create_storage(
                gpu_map[ex_idx], 'pupil_grad_eval_states_ex_%s' % ex_idx))
            optimizer_grad_pupil_storage.append(
                pupil.create_storage(gpu_map[ex_idx], 'optimizer_grad_states_ex_%s' % ex_idx))
        return trainable, pupil_grad_eval_pupil_storage, optimizer_grad_pupil_storage, savers

    def _add_standard_train_hooks(self):
        self._hooks['pupil_grad_eval_inputs'] = self._pupil_grad_eval_inputs
        self._hooks['pupil_grad_eval_labels'] = self._pupil_grad_eval_labels
        self._hooks['optimizer_grad_inputs'] = self._optimizer_grad_inputs
        self._hooks['optimizer_grad_labels'] = self._optimizer_grad_labels
        self._hooks['pupil_savers'] = self._pupil_savers