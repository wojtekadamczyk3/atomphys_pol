import csv
import io
import urllib
import urllib.request
from fractions import Fraction
from typing import List


def remove_annotations(s: str) -> str:
    """remove annotations from energy strings in NIST ASD"""
    # re_energy = re.compile("-?\\d+\\.\\d*|$")
    # return re_energy.findall(s)[0]

    # this is about 3.5× faster than re.findall, but it's less flexible
    # overall this can make a several hundred ms difference when loading
    return s.strip("()[]aluxyz +?").replace("&dagger;", "")


def fetch_states(atom):
    url = "https://physics.nist.gov/cgi-bin/ASD/energy1.pl"
    values = {
        "spectrum": atom,
        "units": 2,  # energy units {0: cm^-1, 1: eV, 2: Ry}
        "format": 3,  # format {0: HTML, 1: ASCII, 2: CSV, 3: TSV}
        "multiplet_ordered": 1,  # energy ordred
        "term_out": "on",  # output the term symbol string
        "conf_out": "on",  # output the configutation string
        "level_out": "on",  # output the energy level
        "unc_out": 0,  # uncertainty on energy
        "j_out": "on",  # output the J level
        "g_out": "on",  # output the g-factor
        "lande_out": "off",  # output experimentally measured g-factor
    }

    get_postfix = urllib.parse.urlencode(values)
    with urllib.request.urlopen(url + "?" + get_postfix) as response:
        response = response.read()

    data = csv.DictReader(
        io.StringIO(response.decode()), dialect="excel-tab", restkey="None"
    )

    return data


def parse_states(data: List[dict]):
    return [
        {
            "energy": remove_annotations(state["Level (Ry)"]) + " Ry",
            "term": state["Term"] + state["J"],
            "configuration": state["Configuration"],
            "J": Fraction(state["J"]),
            "g": float(state["g"]),
        }
        for state in data
    ]


def fetch_transitions(atom):
    # the NIST url and GET options.
    url = "http://physics.nist.gov/cgi-bin/ASD/lines1.pl"
    values = {
        "spectra": atom,
        "format": 3,  # format {0: HTML, 1: ASCII, 2: CSV, 3: TSV}
        "en_unit": 2,  # energy units {0: cm^-1, 1: eV, 2: Ry}
        "line_out": 2,  # only with {1: transition , 2: level classifications}
        "show_av": 5,
        "allowed_out": 1,
        "forbid_out": 1,
        "enrg_out": "on",
    }

    get_postfix = urllib.parse.urlencode(values)
    with urllib.request.urlopen(url + "?" + get_postfix) as response:
        # when there are no transitions ASD returns a texl/html page with the
        # error message "No lines are available in ASD with the parameters selected"
        # rather than the expected text/plain when using format=3
        if response.headers.get_content_type() != "text/plain":
            print(response.headers.get_content_type())
            return []

        response = response.read()

    data = csv.DictReader(io.StringIO(response.decode()), dialect="excel-tab")
    data_with_transition_probabilities = [
        transition for transition in data if transition["Aki(s^-1)"]
    ]

    return data_with_transition_probabilities
