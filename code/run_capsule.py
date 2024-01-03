"""
Main file to execute the smartspim segmentation
in code ocean
"""

import os
from glob import glob
from pathlib import Path
from typing import List, Tuple

from aind_smartspim_quantification import quantification
from aind_smartspim_quantification.params.quantification_params import \
    get_yaml_config
from aind_smartspim_quantification.utils import utils


def get_data_config(
    data_folder: str,
    processing_manifest_path: str = "segmentation_processing_manifest*.json",
    data_description_path: str = "data_description.json",
) -> Tuple:
    """
    Returns the first smartspim dataset found
    in the data folder

    Parameters
    -----------
    data_folder: str
        Path to the folder that contains the data

    processing_manifest_path: str
        Path for the processing manifest

    data_description_path: str
        Path for the data description

    Returns
    -----------
    Tuple[Dict, str]
        Dict: Empty dictionary if the path does not exist,
        dictionary with the data otherwise.

        Str: Empty string if the processing manifest
        was not found
    """

    # Returning first smartspim dataset found
    # Doing this because of Code Ocean, ideally we would have
    # a single dataset in the pipeline

    derivatives_dict = utils.read_json_as_dict(
        f"{data_folder}/{processing_manifest_path}"
    )
    data_description_dict = utils.read_json_as_dict(
        f"{data_folder}/{data_description_path}"
    )

    smartspim_dataset = data_description_dict["name"]

    return derivatives_dict, smartspim_dataset


def set_up_pipeline_parameters(pipeline_config: dict, default_config: dict):
    """
    Sets up smartspim stitching parameters that come from the
    pipeline configuration

    Parameters
    -----------
    smartspim_dataset: str
        String with the smartspim dataset name

    pipeline_config: dict
        Dictionary that comes with the parameters
        for the pipeline described in the
        processing_manifest.json

    default_config: dict
        Dictionary that has all the default
        parameters to execute this capsule with
        smartspim data

    Returns
    -----------
    Dict
        Dictionary with the combined parameters
    """
    default_config["fused_folder"] = os.path.abspath(
        f"{pipeline_config['quantification']['fused_folder']}"
    )
    default_config["stitched_s3_path"] = pipeline_config["stitching"]["s3_path"]
    default_config["channel_name"] = pipeline_config["quantification"]["channel"]
    default_config["save_path"] = os.path.abspath(
        f"{pipeline_config['quantification']['save_path']}/quant_{pipeline_config['quantification']['channel']}"
    )
    default_config["input_params"]["downsample_res"] = pipeline_config["registration"][
        "input_scale"
    ]
    default_config["input_params"][
        "detected_cells_xml_path"
    ] = f"{default_config['cell_segmentation_folder']}/"
    default_config["input_params"][
        "ccf_transforms_path"
    ] = f"{default_config['ccf_registration_folder']}/"

    return default_config


def validate_capsule_inputs(input_elements: List[str]) -> List[str]:
    """
    Validates input elemts for a capsule in
    Code Ocean.

    Parameters
    -----------
    input_elements: List[str]
        Input elements for the capsule. This
        could be sets of files or folders.

    Returns
    -----------
    List[str]
        List of missing files
    """

    missing_inputs = []
    for required_input_element in input_elements:
        required_input_element = Path(required_input_element)

        if not required_input_element.exists():
            missing_inputs.append(str(required_input_element))

    return missing_inputs


def run():
    """
    Main function to execute the smartspim quantification
    in code ocean
    """

    # Absolute paths of common Code Ocean folders
    data_folder = os.path.abspath("../data")
    results_folder = os.path.abspath("../results")
    scratch_folder = os.path.abspath("../scratch")

    # It is assumed that these files
    # will be in the data folder
    required_input_elements = []

    missing_files = validate_capsule_inputs(required_input_elements)

    if len(missing_files):
        raise ValueError(
            f"We miss the following files in the capsule input: {missing_files}"
        )

    pipeline_config, smartspim_dataset_name = get_data_config(data_folder=data_folder)

    # get default configs
    default_config = get_yaml(
        os.path.abspath(
            "./aind_smartspim_quantification/params/default_quantify_config.yaml"
        )
    )

    ccf_folder = glob(f"{data_folder}/ccf_*")

    if len(ccf_folder):
        ccf_folder = ccf_folder[0]

    # add paths to default_config
    default_config["ccf_registration_folder"] = os.path.abspath(ccf_folder)
    default_config["cell_segmentation_folder"] = os.path.abspath(
        f"{data_folder}/cell_{pipeline_config['quantification']['channel']}"
    )

    # combine configs
    smartspim_config = set_up_pipeline_parameters(
        pipeline_config=pipeline_config, default_config=default_config
    )

    smartspim_config["name"] = smartspim_dataset_name

    quantification.main(
        data_folder=Path(data_folder),
        output_quantified_folder=Path(results_folder),
        intermediate_quantified_folder=Path(scratch_folder),
        smartspim_config=smartspim_config,
    )


if __name__ == "__main__":
    run()