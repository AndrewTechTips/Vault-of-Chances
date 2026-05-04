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

tab1, tab2 = st.tabs(["Formular 1: Alegere Teme", "Formular 2: Trimitere Rezolvări"])

# ═══════════════════════════════════════════════════════════════
# TAB 1: ALEGERE TEME
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.header("Teme pentru examenul de \"Teoria Probabilităților și elemente de statistică matematică\"")
    st.info("Înainte de a alege exercițiile, asigură-te că introduci datele tale corect.")
    st.markdown(
        "[👉 **Click aici pentru lista de exerciții**](https://drive.google.com/file/d/1j55dPT0ElRtnC2-OEny6ObbZExTaFP8x/view?usp=drivesdk)")
    st.markdown(
        "[📅 **Click aici pentru modul de notare și termenele limită**](https://drive.google.com/file/d/1Rhs99UojJB2N0METqw0wz7M62MXsMb2Q/view?usp=drivesdk)")
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

                        for key in ['f1_nume', 'f1_prenume', 'f1_grupa', 'f1_tel', 'f1_email', 'f1_spec', 'p1', 'p2']:
                            if key in st.session_state:
                                del st.session_state[key]

                        time.sleep(3)
                        st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 2: TRIMITERE REZOLVARI
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.header("Trimite Rezolvările (Link YouTube)")

    studenti_dict = {}
    for idx, row in df.iterrows():
        email_extras = str(row['Email']).strip()
        link_existent = str(row['Link_Video_1']).strip()

        if email_extras and link_existent in ["", "nan", "None"]:
            nume_complet = f"{row['Numele']} {row['Prenumele']}"

            if nume_complet in studenti_dict:
                nume_complet += f" (Grupa {row['Grupa']})"

            studenti_dict[nume_complet] = email_extras

    if not studenti_dict:
        st.success("🎉 Toți studenții înscriși și-au încărcat deja rezolvările! (Sau nu există încă nicio rezervare).")
    else:
        lista_studenti_afisata = ["Selectează..."] + sorted(studenti_dict.keys())
        student_selectat = st.selectbox("Caută-ți numele în listă (poți tasta direct):", lista_studenti_afisata)

        if student_selectat != "Selectează...":
            email_extras = studenti_dict[student_selectat]
            idx_student = df[df['Email'] == email_extras].index[0]

            p1_asignat = int(float(str(df.at[idx_student, 'Problema_1'])))

            p2_brut = str(df.at[idx_student, 'Problema_2']).strip()
            are_doua_probleme = p2_brut not in ["Neales", "", "nan", "None"]
            p2_asignat = int(float(p2_brut)) if are_doua_probleme else "Neales"

            st.write("---")
            st.info("Confirmă că acestea sunt datele tale înainte de a trimite link-urile.")

            col_ident_1, col_ident_2 = st.columns(2)
            with col_ident_1:
                st.text_input("Email", value=df.at[idx_student, 'Email'], disabled=True)
            with col_ident_2:
                st.text_input("Telefon", value=df.at[idx_student, 'Telefon'], disabled=True)

            msg_probleme = f"**{p1_asignat}**" if not are_doua_probleme else f"**{p1_asignat}** și **{p2_asignat}**"
            st.write(f"👉 Ai de predat exercițiile: {msg_probleme}")

            with st.form("form_video", clear_on_submit=False):
                st.write("Introdu link-urile video de pe YouTube:")
                link_v1 = st.text_input(f"Link video pentru exercițiul {p1_asignat}", key="f2_v1")

                link_v2 = ""
                if are_doua_probleme:
                    link_v2 = st.text_input(f"Link video pentru exercițiul {p2_asignat}", key="f2_v2")

                submit_video = st.form_submit_button("Trimite Rezolvările")

                if submit_video:
                    if not link_v1:
                        st.error(f"Link-ul pentru problema {p1_asignat} este obligatoriu!")
                    elif are_doua_probleme and not link_v2:
                        st.error(
                            f"Ai rezervat 2 probleme. Link-ul pentru problema {p2_asignat} este și el obligatoriu!")
                    else:
                        df_update = citeste_sheet()
                        idx_upd = df_update[df_update['Email'] == email_extras].index[0]

                        df_update.at[idx_upd, 'Link_Video_1'] = link_v1.strip()
                        if are_doua_probleme:
                            df_update.at[idx_upd, 'Link_Video_2'] = link_v2.strip()

                        update_sheet(df_update)

                        st.success("✅ Rezolvările tale au fost salvate cu succes în baza de date!!")

                        for key in ['f2_v1', 'f2_v2']:
                            if key in st.session_state:
                                del st.session_state[key]

                        time.sleep(3)
                        st.rerun()