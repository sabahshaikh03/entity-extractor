import pytest

from app.modules.ask_viridium_ai.services.ask_viridium_ai import AskViridium
from global_constants import GlobalConstants
from utils.logger import Logging

global_constants = GlobalConstants
logger = Logging(global_constants).get_logger()

ask_viridium = AskViridium(logger, global_constants)


@pytest.fixture
def ask_viridium_ai():
    return ask_viridium


def test_init_ask_viridium_ai(ask_viridium_ai):
    assert isinstance(ask_viridium_ai, AskViridium), "Not of type AskViridium "


testbed = [
    ("Deionized Water", "Fisher Diagnostics"),
    ("MOBILGREASE XHP 222 (2015A0202530)", "ExxonMobil (China) Investment Co., Ltd."),
    ("", "Fisher Scientific"),
    ("Agron", "Praxair, Inc."),
    ("VWR Spec-Wipe 7 Wipers", "Contec, Inc."),
    ("Nitric Acid", ""),
    ("Nitric acid", "Guangdong Guanghua Sci-Tech Co., Ltd"),
    ("Isopropyl Alcohol", ""),
    ("1H,1H-PERFLUOROBUTANE (PC5328)", "Apollo Scientific Ltd"),
    ("3M Novec 72DE Engineered Fluid (98-0212-2966-5)", "3M"),
    (
        "SWISSCUT ORTHO NF-X 22",
        "MOTOREX AG LANGENTHAL",
    ),
]


@pytest.mark.parametrize("material_name, manufacturer_name", testbed)
def test_query_ask_viridium_ai(material_name, manufacturer_name, ask_viridium_ai):

    result = ask_viridium_ai.query(
        material_name=material_name, manufacturer_name=manufacturer_name
    )

    assert isinstance(result, dict), "Query Result is not a dictionary"

    assert len(result) > 0, "Query result is empty"

    assert result["decision"] in [
        "PFAS (No)",
        "PFAS (Yes)",
        "Undetermined",
    ], "Query Decision is invalid"
