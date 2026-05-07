import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import time
import re

tz_ro = pytz.timezone('Europe/Bucharest')
st.set_page_config(page_title="Platformă Statistică Matematică", layout="centered")

URL_TABEL = "https://docs.google.com/spreadsheets/d/1iW5EzJv7lEgf-E5Lfq6pW6X8tY7JCuaCPLwq2sDCHfk/edit"

conn = st.connection("gsheets", type=GSheetsConnection)


def citeste_sheet():
    df = conn.read(spreadsheet=URL_TABEL, worksheet="Date_Studenti", ttl=0).astype(str)
    df = df.replace("nan", "")
    return df


def update_sheet(new_df):
    conn.update(spreadsheet=URL_TABEL, worksheet="Date_Studenti", data=new_df)
    st.cache_data.clear()


def calculeaza_probleme_disponibile(df):
    # Setat pentru 223 de probleme
    probleme_totale = list(range(1, 224))
    p1_list = df['Problema_1'].tolist()
    p2_list = df['Problema_2'].tolist()

    probleme_luate = set()
    for p in p1_list + p2_list:
        try:
            probleme_luate.add(int(float(str(p).strip())))
        except (ValueError, TypeError):
            pass

    return [p for p in probleme_totale if p not in probleme_luate]


df = citeste_sheet()
probleme_disponibile = calculeaza_probleme_disponibile(df)

# Secțiunea principală: Alegere Teme
st.header("Teme (Alegerea Exercițiilor) pentru examenul de \"Teoria Probabilităților și elemente de statistică matematică\"")
st.info("Înainte de a alege exercițiile, asigură-te că introduci datele tale corect.")

# Link-uri importante
st.markdown(
    "[👉 **Click aici pentru lista de exerciții**](https://drive.google.com/file/d/1ylAGEwDh2WFdGZqYGnW2Cc07loEHqE4d/view?usp=drivesdk)")
st.markdown(
    "[📊 **IMPORTANT: INAINTE DE ALEGE EXERCITIILE VERIFICA AICI DACA EXERCITIILE NU AU MAI FOST ALESE DE ALTCINEVA INAINTE**](https://docs.google.com/spreadsheets/d/1iW5EzJv7lEgf-E5Lfq6pW6X8tY7JCuaCPLwq2sDCHfk/edit?gid=0#gid=0)")
st.markdown(
    "[📅 **Click aici pentru modul de notare și termenele limită**](https://drive.google.com/file/d/1pAsljAYtgVLVb0Us7AuX72GUElp0_bei/view)")
st.write("---")

if not probleme_disponibile:
    st.warning("Toate problemele au fost rezervate!")
else:
    with st.form("form_alegere", clear_on_submit=False):
        col_nume, col_prenume = st.columns(2)
        with col_nume:
            nume_input = st.text_input("Numele", key="f1_nume")
        with col_prenume:
            prenume_input = st.text_input("Prenumele", key="f1_prenume")

        col_grupa, col_tel = st.columns(2)
        with col_grupa:
            grupa = st.selectbox("Grupa", ["Selectează...", "1", "2", "3", "4", "An complementar"], key="f1_grupa")
        with col_tel:
            telefon_input = st.text_input("Nr. de telefon", key="f1_tel")

        email_input = st.text_input("Adresa de mail", key="f1_email")
        specializare = st.selectbox("Specializarea", ["Selectează...", "Info An 2", "Info An 3", "An complementar"],
                                    key="f1_spec")

        st.write("---")
        st.info(
            "💡 **HINT:** Dacă dorești să alegi **o singură problemă**, selectează numărul ei la prima opțiune, iar la a doua opțiune alege **'Niciuna (Aleg doar 1)'**.")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            prob1 = st.selectbox("Numărul primului exercițiu ales (Obligatoriu)",
                                 ["Selectează..."] + probleme_disponibile, key="p1")
        with col_p2:
            prob2 = st.selectbox("Numărul celui de-al 2-lea exercițiu ales",
                                 ["Selectează...", "Niciuna (Aleg doar 1)"] + probleme_disponibile, key="p2")

        submit_alegere = st.form_submit_button("Trimite Alegerea")

    if submit_alegere:
        eroare = None

        nume = nume_input.strip().title()
        prenume = prenume_input.strip().title()
        telefon = telefon_input.strip().replace(" ", "")
        email = email_input.strip().lower()

        if not all([nume, prenume, telefon, email]):
            eroare = "Te rog completează toate datele personale!"
        elif grupa == "Selectează...":
            eroare = "Te rog selectează grupa!"
        elif specializare == "Selectează...":
            eroare = "Te rog selectează specializarea!"
        elif not re.match(r"^\+?\d{9,15}$", telefon):
            eroare = "Numărul de telefon este invalid! Acesta trebuie să conțină doar cifre (și opțional semnul +)."
        elif not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            eroare = "Adresa de email nu are un format valid!"
        elif prob1 == "Selectează...":
            eroare = "Te rog alege măcar primul exercițiu!"
        elif prob2 == "Selectează...":
            eroare = "Te rog alege al 2-lea exercițiu sau selectează 'Niciuna (Aleg doar 1)'."
        elif prob1 == prob2:
            eroare = "Cele două exerciții alese trebuie să fie diferite!"

        if eroare:
            st.error(eroare)
        else:
            df_live = citeste_sheet()

            nume_complet_curent = f"{nume} {prenume}".lower()
            nume_existente = [f"{str(row['Numele']).strip().lower()} {str(row['Prenumele']).strip().lower()}" for
                              _, row in df_live.iterrows()]

            if nume_complet_curent in nume_existente:
                st.error(
                    f"Un student cu numele {nume} {prenume} a făcut deja o rezervare! Dacă aceasta este o eroare, contactează administratorul.")
            elif email in [str(e).lower().strip() for e in df_live['Email'].tolist()]:
                st.error("Această adresă de mail a fost deja folosită pentru o rezervare!")
            else:
                luate_live = set()
                for p in df_live['Problema_1'].tolist() + df_live['Problema_2'].tolist():
                    try:
                        luate_live.add(int(float(str(p).strip())))
                    except (ValueError, TypeError):
                        pass

                conflict_p1 = int(prob1) in luate_live
                conflict_p2 = False if prob2 == "Niciuna (Aleg doar 1)" else int(prob2) in luate_live

                if conflict_p1 or conflict_p2:
                    st.error("Una dintre probleme a fost rezervată acum câteva secunde. Te rog alege alta.")
                    time.sleep(2)
                    st.rerun()
                else:
                    timestamp_curent = datetime.now(tz_ro).strftime("%Y-%m-%d %H:%M:%S")
                    val_prob_2 = "Neales" if prob2 == "Niciuna (Aleg doar 1)" else int(prob2)

                    rand_nou = pd.DataFrame([{
                        "Numele": nume,
                        "Prenumele": prenume,
                        "Grupa": grupa,
                        "Telefon": telefon,
                        "Email": email,
                        "Specializarea": specializare,
                        "Problema_1": int(prob1),
                        "Problema_2": val_prob_2,
                        "Timestamp_Rezervare": timestamp_curent,
                        "Link_Video_1": "",
                        "Link_Video_2": ""
                    }])

                    df_actualizat = pd.concat([df_live, rand_nou], ignore_index=True)
                    update_sheet(df_actualizat)

                    msg_ex = f"{int(prob1)}" if val_prob_2 == "Neales" else f"{int(prob1)} și {val_prob_2}"
                    st.success(
                        f"✅ Rezervare înregistrată cu succes la ora {timestamp_curent}! Exerciții alese: {msg_ex}")
                    st.balloons()

                    # Ștergem datele din formular la succes
                    for key in ['f1_nume', 'f1_prenume', 'f1_grupa', 'f1_tel', 'f1_email', 'f1_spec', 'p1', 'p2']:
                        if key in st.session_state:
                            del st.session_state[key]

                    time.sleep(3)
                    st.rerun()