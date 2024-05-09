#! /usr/bin/env python3
"""Executable script to simulate kinetic data using the KineticModel
class.

"""
import math
import os
import appdirs
import itertools
import argparse
import pickle
import kinmodel
import kinmodel.constants as constants

PAR_ERR_TEXT = "Invalid parameter input format"
RANGE_IND = ".."


def model_kinetics():

    model_search_dirs = [
        os.path.join(os.getcwd(), constants.MODEL_DIR_NAME),
        os.path.join(appdirs.user_data_dir(
                constants.APP_NAME,
                constants.APP_AUTHOR),
                constants.MODEL_DIR_NAME),
        os.path.dirname(kinmodel.models.__file__)
        ]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "model_name",
        help=("Name of model to use (see fit_kinetics.py -h for list of "
              "default models)"))
    parser.add_argument(
        "time",
        help="Total time for simulation",
        type=float)
    parser.add_argument(
        "-ks", "--ks",
        help="List of rate constants and parameters for model",
        nargs="+")
    parser.add_argument(
        "-l", "--load",
        help="Pickle file from which to load ks")
    parser.add_argument(
        "-cs", "--concs",
        help="List of starting concentrations",
        nargs="+")
    parser.add_argument(
        "-f", "--filename",
        help="Root filename for output (no extension)")
    parser.add_argument(
        "-n", "--sim_number",
        help="Number of simulations (for parameter ranges, default 2^n)",
        type=int)
    parser.add_argument(
        "-tp", "--text_output_points",
        help=("Number of points for curves in text output (not pdf) "
              "(default = 3000)"),
        type=int, default=3000)
    parser.add_argument(
        "-so", "--summary_output",
        help="Excludes conc vs time data from text output",
        action='store_true')
    parser.add_argument(
        "-pp", "--plot_output_points",
        help="Number of points for curves in output (pdf) (default = 1000)",
        type=int, default=1000)
    parser.add_argument(
        "-u", "--units",
        help=("Time and concentration units, each as a single word"),
        nargs=2, type=str)
    args = parser.parse_args()

    if args.ks:
        # Load parameters from command line, including ranges.
        loaded_parameters = args.ks + args.concs
        num_ranges = len([t for t in loaded_parameters if RANGE_IND in t])
        if args.sim_number:
            sim_number = args.sim_number
        else:
            sim_number = 2**(num_ranges)

        if num_ranges > 0:
            sims_per_range = math.floor(sim_number**(1/num_ranges))
        else:
            sims_per_range = None

        if sims_per_range == 1:
            raise ValueError("Too few simulations specified for number of "
                             "ranged parameters.")

        parameters = []
        for parameter in loaded_parameters:
            parameter_range = parameter.split(RANGE_IND)
            if len(parameter_range) == 1:
                try:
                    parameters.append([float(parameter_range[0])])
                except ValueError:
                    print(PAR_ERR_TEXT)
            elif len(parameter_range) == 2:
                try:
                    p0 = float(parameter_range[0])
                    p1 = float(parameter_range[1])
                    delta = (p1-p0)/(sims_per_range-1)
                    parameters.append([])
                    for n in range(sims_per_range):
                        parameters[-1].append(p0 + delta*n)
                except ValueError:
                    print(PAR_ERR_TEXT)
            else:
                raise ValueError(PAR_ERR_TEXT)
        all_parameters = list(itertools.product(*parameters))
    elif args.load:
        # Load bootstrapped parameters from pickle file.
        with open(args.load, 'rb') as file:
            loaded_reg_info = pickle.load(file)
        all_ks = [list(x) for x in loaded_reg_info['boot_fit_ks']]
        concs = [float(x) for x in args.concs]
        all_parameters = [x + concs for x in all_ks]

    all_models = kinmodel.KineticModel.get_all_models(model_search_dirs)
    model = kinmodel.KineticModel.get_model(args.model_name, all_models)

    # Number of digits to use in filenames.
    index_digits = math.floor(math.log10(len(all_parameters))) + 1
    set_num = 0
    for parameter_set in all_parameters:
        set_num += 1
        ks = list(parameter_set[:model.num_ks])
        concs = list(parameter_set[model.num_ks:])
        if args.filename:
            filename = args.filename + f"_{set_num:0{index_digits}}"
        else:
            filename = None
        kinmodel.simulate_and_output(
                model=model,
                ks=ks,
                concs=concs,
                time=args.time,
                text_num_points=args.text_output_points,
                plot_num_points=args.plot_output_points,
                filename=filename,
                text_full_output=not args.summary_output,
                units=args.units)
