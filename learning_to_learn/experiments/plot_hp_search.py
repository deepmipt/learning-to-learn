import sys
import os

from pathlib import Path  # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[2]
sys.path.append(str(root))
try:
    sys.path.remove(str(parent))
except ValueError:  # Already removed
    pass

from learning_to_learn.useful_functions import convert, apply_func_to_nested, synchronous_sort, create_path, \
    remove_empty_strings_from_list

from learning_to_learn.experiments.plot_helpers import get_parameter_names, plot_hp_search, parse_eval_dir
import argparse
parser = argparse.ArgumentParser()
parser.add_argument(
    "hp_order",
    help="Order of hyper parameters. Hyper parameter names as in run config separated by commas without spaces"
)
parser.add_argument(
    "eval_dir",
    help="Path to evaluation directory containing experiment results. \nTo process several evaluation directories"
         " use following format '<path1>,<path2>,...<pathi>:<pathi+1>,..:..'.\nAll possible combinations of sets"
         " separated by colons (in specified order) will be processed. \nYou have to provide paths relative to "
         "script. Edge characters of <path> can't be '/'"
)
parser.add_argument(
    "-pd",
    "--plot_dir",
    help="Path to directory where plots are going to be saved",
    default='plots',
)
parser.add_argument(
    "-xs",
    "--xscale",
    help="x axis scale. It can be log or linear. Default is linear",
    default='linear',
)
parser.add_argument(
    "-ms",
    "--metric_scales",
    help="Scales for metrics. Available metrics are 'accuracy', 'bpc', 'loss', 'perplexity'. "
         "Scales are provided in following format <metric>:<scale>,<metric>:<scale>. "
         "Default is linear"
)
parser.add_argument(
    "-nlfp",
    "--num_lines_for_plot",
    help="Number of lines per one plot. Default is all lines."
)
parser.add_argument(
    "-nl",
    "--no_line",
    help="Do not link dots with line. Default is True",
    action='store_true'
)
parser.add_argument(
    '-hpnf',
    "--hp_names_file",
    help="File with hyper parameter names. All available files are in the same directory with this script",
    default='hp_plot_names_english.conf'
)
args = parser.parse_args()

AVERAGING_NUMBER = 3

eval_dirs = parse_eval_dir(args.eval_dir)
for eval_dir in eval_dirs:
    print(eval_dir)
    plot_dir = os.path.join(*list(os.path.split(eval_dir)[:-1]) + [args.plot_dir])
    hp_plot_order = args.hp_order.split(',')

    metric_scales = dict()
    if args.metric_scales is not None:
        for one_metric_scale in args.metric_scales.split(','):
            [metric, scale] = one_metric_scale.split(':')
            metric_scales[metric] = scale

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    plot_parameter_names = get_parameter_names(args.hp_names_file)
    xscale = args.xscale
    no_line = args.no_line

    plot_hp_search(
        eval_dir,
        plot_dir,
        hp_plot_order,
        args.hp_names_file,
        metric_scales,
        args.xscale,
        args.no_line,
    )
