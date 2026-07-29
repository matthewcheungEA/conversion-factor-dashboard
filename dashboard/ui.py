import streamlit as st
from dashboard.combustion_properties import hhv_mol, number_atoms, sj_library

class DashboardInput():
    def __init__(self):
        """
        This is the dashboard input page.
        """
        col1, col2 = self.title()
        (
            self.input_pct,
            self.input_species,
            self.composition_valid,
        ) = self.input(col1)

        (self.input_P, self.input_T, self.input_phi, self.input_pct_o2 ) = self.properties(col2)

        self.calculation_button()


    def title(self):
        """
        This is the title of the dashboard.
        :return:
        """
        st.set_page_config(page_title="Conversion Factors Calculator")
        st.title("Conversion Factors Calculator")
        st.markdown(
            "This tool is developed to understand conversion factor (CF)"
            "CF is a dimensionless multiplier that adjusts concentration-based emissions reporting to account for differences in fuel composition and thermal energy output between fuels."
            "It should be noted that conversion factors or ELV after multiplying FCF does not necessarily means the ELV of the fuel but a reference guidance for ELV in environmental regulations. "
        )
        st.subheader("Fuel composition (mol %)")
        col1, col2 = st.columns(2, gap="small")
        return col1, col2

    def input(self, col1):
        """
        When adding new species, please add them according to their charateristics,
        :param col1:
        :return:
        """
        common = [ "CO",  "H2", "NH3"]
        refinery = ["CH4", "C2H6", "C2H4", "C2H2", "C3H8", "C3H6", "iC4H10", "C4H10", "C4H8-1", "iC4H8", "C4H8-2", "C4H6", "nC5H12"]
        inert = ["N2", "O2", "CO2", "Ar", "He"]
        species = common + refinery + inert

        with col1:
            pct = {}
            st.markdown("Common gases")
            for sp in common:
                pct[sp] = st.number_input(f"{sp} (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key=sp)


            st.markdown("Refinery gases")
            for sp in refinery:
                pct[sp] = st.number_input(f"{sp} (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key=sp)


            st.markdown("Inert gases")
            st.caption("Please be noted that these gases are technically not inert in real life combustion, but assume to be for simplification")
            for sp in inert:
                pct[sp] = st.number_input(f"{sp} (%)",  min_value=0.0, max_value=100.0, value=0.0, step=0.1, key=sp)
            total = sum(pct.values())

            if total <= 0:
                st.warning(
                    "Enter at least one component before calculating."
                )
                composition_valid = False
            else:
                st.info(
                    f"Input total = {total:.2f}. "
                    "The composition will be automatically normalised."
                )
                composition_valid = True

            return pct, species, composition_valid

    def properties(self, col2):
        """
        Lets users input their properties.
        :param col2:
        :return:
        """
        with col2:
            p = st.number_input("Pressure (Pa)" , value=101325.0)
            t = st.number_input("Temperature (K)", value=273.0)
            phi = st.number_input("equivalence ratio (-)", value=1.0)
            air_content = st.number_input("% of air", value=21.0, min_value=0.1, max_value=100.0)
            pct_o2 = air_content/100
        return p, t, phi, pct_o2

    def calculation_button(self):
        """
        Runs the calculations when the calculate button is pressed.
        :return:
        """
        calculate = st.button(
            "Calculate fuel correction factor",
            type="primary",
            disabled=not self.composition_valid,
        )

        if calculate:
            try:
                calculations = Calculations()
                total_lhv = calculations.lhv_calculation(self.input_pct)
                v_dry = calculations.stochiometric_calculation(
                    self.input_pct,
                    self.input_pct_o2,
                )
                FF_NG = calculations.ff_ng(self.input_pct_o2)
                CF = calculations.cf_calculation(v_dry, total_lhv, FF_NG)
                Output(CF, total_lhv)

            except (ValueError, KeyError, ZeroDivisionError) as error:
                st.error(f"Calculation failed: {error}")

class Calculations():
    def __init__(self):
        """
        Add here
        """

    def lhv_calculation(self, pct):
        """
        Add here
        :param pct:
        :return:
        """
        total = sum(pct.values())
        total_lhv = 0.0
        A_H2O = 0.045064

        for sp, value in pct.items():
            x = value / total
            hhv = hhv_mol(sp)
            atoms = number_atoms({sp: 1})
            H = atoms.get("H", 0)
            water_loss = (H / 2) * A_H2O
            lhv = hhv - water_loss
            total_lhv += x * lhv
        return total_lhv

    def stochiometric_calculation(self, pct, pct_o2):
        """
        Add here.
        :param pct:
        :param pct_O2:
        :return:
        """
        total = sum(pct.values())
        mole_fractions = {
            species: amount / total
            for species, amount in pct.items()
        }

        atoms = number_atoms(mole_fractions)
        sj = sj_library(pct)
        sj_sum = 0.0

        for sp, value in pct.items():
            x_i = value / total
            sji = sj.get(sp, 0.0)
            sj_sum += x_i * sji

        Z = 1 - sj_sum ** 2

        C = atoms.get("C", 0)
        H = atoms.get("H", 0)
        O = atoms.get("O", 0)
        N = atoms.get("N", 0)
        S = atoms.get("S", 0)
        Ar = atoms.get("Ar", 0.0)
        He = atoms.get("He", 0.0)

        CO2 = C
        H2O = H / 2
        N2_fuel = N / 2
        SO2 = S
        O_needed = 2*CO2 + H2O + 2*SO2 - O
        O2_required = (O_needed)/2
        N2_air = O2_required * (1- pct_o2) / pct_o2

        mol_dry = N2_air + N2_fuel + CO2 + SO2 + Ar + He
        vm = Z * 0.02241383
        v_dry = mol_dry * vm

        return v_dry

    def ff_ng(self,pct_o2):
        """
        CH4 92%, C2H6 3.25%, C3H8 0.75%, C4H10 0.25%, N2 3%, CO2 0.75%
        If change %, change directly from below
        :param pct_air:
        :return:
        """
        C = 0.92*1 + 0.0325*2 + 0.0075*3 + 0.0025*4
        H = 4*0.92 + 6*0.0325 + 8*0.0075 + 10*0.0025
        Z = 1 - (0.92*0.04886 + 0.0325*0.0997 + 0.0075*0.1465 + 0.0025*0.2022 + 0.03*0.0214 + 0.0075*0.0821)**2
        molar_vol_ng = Z * 0.02241383
        vol_ng = (0.03 + 0.0075 + C + (C + H / 4) * (1 - pct_o2) / pct_o2 )* molar_vol_ng  # m3/mol
        A_H2O = 45.064 # kJ/mol
        HHV = 0.92*0.89292 + 0.0325* 1.564 + 0.0075*2.22403 + 0.0025*2.883 #MJ/mol
        lhv_mol_ng = HHV - (H / 2) * A_H2O / 1000
        ff_ng = vol_ng / lhv_mol_ng
        return ff_ng

    def cf_calculation(self,v_dry,total_lhv, ff_ng):
        """
        NG gas composition was taken from BS ISO 6976
        :param Volume_dry: Dry Flue gas Volume
        :param total_LHV:
        :return:
        """
        if total_lhv <= 0:
            st.error("The mixture must contain a fuel with a positive LHV.")
            raise ValueError(
                "The mixture must contain a fuel with a positive LHV."
            )

        ff = v_dry/total_lhv
        cf = ff_ng / ff
        return cf

class Output():
    def __init__(self, cf, total_lhv):
        """
        This is the Output dashboard final page.
        :param cf:
        :param total_lhv:
        """
        self.properties(cf, total_lhv)

    def properties(self, cf, total_lhv):
        """
        add info here
        :param cf:
        :param total_lhv:
        :return:
        """
        self.col1, self.col2 = st.columns(2)
        with self.col1:
            st.metric(
                "Lower heating value",
                f"{total_lhv:.3f} MJ/mol",
            )

        with self.col2:
            st.metric(
                "Conversion factor",
                f"{cf:.3f}",
            )
