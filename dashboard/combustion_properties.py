"""Combustion-property data used by the fuel correction factor dashboard.

Gross calorific values and ISO 6976 summation factors are stated at a
reference temperature of 0 C
"""

from collections.abc import Mapping



hhv_mol_dict = {
    "H2": 0.28664,
    "CO": 0.28280,
    "CH4": 0.89292,
    "C2H6": 1.56435,
    "C2H4": 1.41355,
    "C2H2": 1.30186,
    "C3H8": 2.22403,
    "C3H6": 2.06157,
    "iC4H10": 2.87421,
    "C4H10": 2.88335,
    "C4H8-1": 2.72157,
    "iC4H8": 2.70488,
    "C4H8-2": 2.71109,
    "C4H6": 2.54414,
    "nC5H12": 3.54291,
    "NH3": 0.38457,
    "N2": 0.0,
    "O2": 0.0,
    "CO2": 0.0,
    "He": 0.0,
    "Ar": 0.0,
}



atoms_dict = {
    "H2": {"H": 2},
    "CO": {"C": 1, "O": 1},
    "CH4": {"C": 1, "H": 4},
    "C2H6": {"C": 2, "H": 6},
    "C2H4": {"C": 2, "H": 4},
    "C2H2": {"C": 2, "H": 2},
    "C3H8": {"C": 3, "H": 8},
    "C3H6": {"C": 3, "H": 6},
    "iC4H10": {"C": 4, "H": 10},
    "C4H10": {"C": 4, "H": 10},
    "C4H8-1": {"C": 4, "H": 8},
    "iC4H8": {"C": 4, "H": 8},
    "C4H8-2": {"C": 4, "H": 8},
    "C4H6": {"C": 4, "H": 6},
    "nC5H12": {"C": 5, "H": 12},
    "NH3": {"N": 1, "H": 3},
    "N2": {"N": 2},
    "O2": {"O": 2},
    "CO2": {"C": 1, "O": 2},
    "He": {"He": 1},
    "Ar": {"Ar": 1},
}
sj_dict = {
    "H2": -0.0100,
    "CO": 0.0258,
    "CH4": 0.04886,
    "C2H6": 0.0997,
    "C2H4": 0.0868,
    "C2H2": 0.0936,
    "C3H8": 0.1465,
    "C3H6": 0.1381,
    "iC4H10": 0.1885,
    "C4H10": 0.2022,
    "C4H8-1": 0.1964,
    "iC4H8": 0.1966,
    "C4H8-2": 0.2072,
    "C4H6": 0.1993,
    "nC5H12": 0.2586,
    "NH3": 0.1230,
    "N2": 0.0214,
    "O2": 0.0311,
    "CO2": 0.0821,
    "He": -0.0100,
    "Ar": 0.0307,
}


def hhv_mol(species: str) -> float:
    """Return the ideal-gas gross calorific value at 0 °C in MJ/mol."""
    try:

        return hhv_mol_dict[species]
    except KeyError as exc:
        raise ValueError(f"Unsupported species for HHV: {species}") from exc


def number_atoms(composition: Mapping[str, float]) -> dict[str, float]:
    """Return elemental totals on the basis supplied by ``composition``.

    For example, ``{"CH4": 0.8, "CO2": 0.2}`` returns the elemental
    totals for 0.8 mol methane and 0.2 mol carbon dioxide.
    """
    totals: dict[str, float] = {}

    for species, amount in composition.items():
        if amount < 0:
            raise ValueError(f"Amount cannot be negative for {species}.")

        try:

            species_atoms = atoms_dict[species]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported species for atom counting: {species}"
            ) from exc

        for element, atom_count in species_atoms.items():
            totals[element] = totals.get(element, 0.0) + amount * atom_count

    return totals


def sj_library(composition: Mapping[str, float]) -> dict[str, float]:
    """Return the 0 °C ISO 6976 summation factors for a composition."""
    factors: dict[str, float] = {}

    for species in composition:
        try:
            factors[species] = sj_dict[species]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported species for summation factor: {species}"
            ) from exc

    return factors
