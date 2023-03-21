"""
Add our Hochfrequenz logo as a watermark to a EBD diagram.
The Hochfrequenz logo will be scaled, so that the it has 80% (final_scaling_factor)
of the smallest dimension of the EBD diagram.
Afterwards it gets placed into the center of the EBD diagram.
"""

import re
from io import BytesIO
from pathlib import Path
from typing import TextIO, Tuple, Union

from lxml import etree  # type:ignore[import]
from svgutils.compose import SVG, Figure  # type:ignore[import]

# Sets the size of the watermark compared to the smaller dimension of the ebd diagram
FINAL_SCALING_FACTOR = 0.8


def convert_dimension_to_float(dimension: str) -> float:
    """
    Looks for the unit "px" in the dimension string and removes it if it is present.
    Finally the dimension string is converted into float.
    :param dimension: dimension string of a svg image
    """

    if dimension[-2:] == "px":
        dimension_float = float(dimension[:-2])
    elif dimension[-2:] == "pt":
        dimension_float = float(dimension[:-2]) * 4 / 3
    elif re.match(r"^[\d.]+$", dimension) is not None:  # assume the default unit is px
        dimension_float = float(dimension)
    else:
        raise ValueError("unsupported unit type")
    return dimension_float


def get_dimensions_of_svg(svg_as_bytes: Union[BytesIO, TextIO]) -> Tuple[float, float]:
    """
    Extract the dimensions of an svg image.
    :param svg_as_bytes:
    _return width_of_svg_in_px, height_of_svg_in_px:
    """
    # pylint: disable=no-member
    tree = etree.parse(svg_as_bytes)  # pylint:disable=c-extension-no-member
    root = tree.getroot()

    # root.attrib["height"] gives a string like "123px"
    # for further usage, we have to remove the unit and convert it to integer
    width_of_svg_in_px = convert_dimension_to_float(root.attrib["width"])
    height_of_svg_in_px = convert_dimension_to_float(root.attrib["height"])

    return width_of_svg_in_px, height_of_svg_in_px


# pylint: disable = c-extension-no-member
def add_watermark(ebd_svg_as_bytes: bytes) -> bytes:
    """
    Scales our hochfrequenz logo and centers it in a given EBD diagram
    :param ebd_svg_as_bytes:
    """
    ebd_width_in_px, ebd_height_in_px = get_dimensions_of_svg(BytesIO(ebd_svg_as_bytes))

    directory_path = Path(__file__).parent
    hochfrequenz_logo_file_name = "hochfrequenz-logo.svg"
    path_to_hf_logo = directory_path / hochfrequenz_logo_file_name

    with open(path_to_hf_logo, encoding="utf-8") as watermark_svg:
        watermark_width_in_px, watermark_height_in_px = get_dimensions_of_svg(watermark_svg)

    if ebd_height_in_px >= ebd_width_in_px:
        scale = (ebd_width_in_px * FINAL_SCALING_FACTOR) / watermark_width_in_px
        move_x = ebd_width_in_px * (1 - FINAL_SCALING_FACTOR) / 2
        move_y = (ebd_height_in_px - (watermark_height_in_px * scale)) / 2
    else:
        scale = (ebd_height_in_px * FINAL_SCALING_FACTOR) / watermark_height_in_px
        move_x = (ebd_width_in_px - (watermark_width_in_px * scale)) / 2
        move_y = ebd_height_in_px * (1 - FINAL_SCALING_FACTOR) / 2

    ebd_with_watermark = Figure(
        ebd_width_in_px,
        ebd_height_in_px,
        SVG(str(path_to_hf_logo)).scale(scale).move(move_x, move_y),
        etree.fromstring(ebd_svg_as_bytes),
    ).tostr()

    # the following lines are needed if we have to create a new test_compare.svg file
    # please do not delete them.
    # Figure(
    #     ebd_width_in_px,
    #     ebd_height_in_px,
    #     SVG(path_to_hf_logo).scale(scale).move(move_x, move_y),
    #     etree.fromstring(ebd_svg_as_bytes),
    # ).save("test_compare.svg")

    # with open("awesome_watermark.svg", "w") as output:
    #     output.write(ebd_with_watermark.decode())

    return ebd_with_watermark