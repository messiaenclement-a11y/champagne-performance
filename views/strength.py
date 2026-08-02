from datetime import date

import pandas as pd
import streamlit as st

from components.layout import page_header
from services.calculations import estimated_1rm
from services.supabase_client import (
    fetch_all,
    get_supabase,
    insert_row,
    insert_rows,
    upsert_rows,
)
from utils.formatting import player_label


page_header(
    "Musculation",
    "Créer un modèle, programmer puis saisir charge et RPE",
)


players = fetch_all(
    "players",
    order="last_name",
    filters={"is_active": True},
)

templates = fetch_all(
    "strength_templates",
    order="name",
)

sessions = fetch_all(
    "strength_sessions",
    order="session_date",
    desc=True,
)


tab_template, tab_schedule, tab_results, tab_history = st.tabs(
    [
        "Créer un modèle",
        "Programmer",
        "Saisir les résultats",
        "Historique",
    ]
)


# -------------------------------------------------------------------
# Créer un modèle
# -------------------------------------------------------------------
with tab_template:
    st.caption(
        "Crée un modèle de séance avec les exercices, "
        "le nombre de séries et le nombre de répétitions."
    )

    template_name = st.text_input(
        "Nom du modèle",
        placeholder="Force bas du corps",
    )

    exercise_count = st.number_input(
        "Nombre d'exercices",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
    )

    exercises = []

    for index in range(int(exercise_count)):
        col_name, col_sets, col_reps = st.columns([3, 1, 1])

        exercise_name = col_name.text_input(
            f"Exercice {index + 1}",
            key=f"exercise_name_{index}",
        )

        sets_count = col_sets.number_input(
            "Séries",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            key=f"sets_count_{index}",
        )

        reps_count = col_reps.number_input(
            "Rép.",
            min_value=1,
            max_value=50,
            value=6,
            step=1,
            key=f"reps_count_{index}",
        )

        exercises.append(
            {
                "exercise_name": exercise_name,
                "sets_count": sets_count,
                "reps_count": reps_count,
            }
        )

    create_template = st.button(
        "Enregistrer le modèle",
        type="primary",
        use_container_width=True,
    )

    if create_template:
        missing_exercise = any(
            not exercise["exercise_name"].strip()
            for exercise in exercises
        )

        if not template_name.strip() or missing_exercise:
            st.error(
                "Le nom du modèle et tous les noms d'exercices "
                "sont obligatoires."
            )

        else:
            template = insert_row(
                "strength_templates",
                {
                    "name": template_name.strip(),
                    "is_active": True,
                },
            )

            exercise_payloads = []

            for index, exercise in enumerate(exercises):
                exercise_payloads.append(
                    {
                        "template_id": template["id"],
                        "exercise_name": (
                            exercise["exercise_name"].strip()
                        ),
                        "sets_count": int(
                            exercise["sets_count"]
                        ),
                        "reps_count": int(
                            exercise["reps_count"]
                        ),
                        "display_order": index + 1,
                    }
                )

            insert_rows(
                "strength_template_exercises",
                exercise_payloads,
            )

            st.success("Modèle enregistré.")
            st.rerun()


# -------------------------------------------------------------------
# Programmer une séance
# -------------------------------------------------------------------
with tab_schedule:
    if not templates:
        st.info("Créez d'abord un modèle.")

    else:
        template_id = st.selectbox(
            "Modèle",
            options=[
                template["id"]
                for template in templates
            ],
            format_func=lambda selected_id: next(
                template["name"]
                for template in templates
                if template["id"] == selected_id
            ),
        )

        session_date = st.date_input(
            "Date",
            value=date.today(),
            key="strength_session_date",
        )

        session_comment = st.text_area(
            "Commentaire",
            key="strength_session_comment",
        )

        schedule_session = st.button(
            "Programmer la séance",
            use_container_width=True,
        )

        if schedule_session:
            session = insert_row(
                "strength_sessions",
                {
                    "template_id": template_id,
                    "session_date": session_date.isoformat(),
                    "comment": (
                        session_comment.strip()
                        or None
                    ),
                    "status": "Planifiée",
                },
            )

            template_exercises = fetch_all(
                "strength_template_exercises",
                order="display_order",
                filters={
                    "template_id": template_id,
                },
            )

            session_exercise_payloads = []

            for exercise in template_exercises:
                session_exercise_payloads.append(
                    {
                        "strength_session_id": session["id"],
                        "exercise_name": (
                            exercise["exercise_name"]
                        ),
                        "sets_count": (
                            exercise["sets_count"]
                        ),
                        "reps_count": (
                            exercise["reps_count"]
                        ),
                        "display_order": (
                            exercise["display_order"]
                        ),
                    }
                )

            insert_rows(
                "strength_session_exercises",
                session_exercise_payloads,
            )

            st.success("Séance programmée.")
            st.rerun()


# -------------------------------------------------------------------
# Saisir les résultats
# -------------------------------------------------------------------
with tab_results:
    if not sessions:
        st.info(
            "Programmez d'abord une séance de musculation."
        )

    elif not players:
        st.info(
            "Aucun joueur actif n'est disponible."
        )

    else:
        session_id = st.selectbox(
            "Séance",
            options=[
                session["id"]
                for session in sessions
            ],
            format_func=lambda selected_id: next(
                (
                    f"{session['session_date']} — "
                    f"{session.get('status', '')}"
                )
                for session in sessions
                if session["id"] == selected_id
            ),
        )

        player_id = st.selectbox(
            "Joueur",
            options=[
                player["id"]
                for player in players
            ],
            format_func=lambda selected_id: player_label(
                next(
                    player
                    for player in players
                    if player["id"] == selected_id
                )
            ),
        )

        session_exercises = fetch_all(
            "strength_session_exercises",
            order="display_order",
            filters={
                "strength_session_id": session_id,
            },
        )

        session_exercise_ids = [
            exercise["id"]
            for exercise in session_exercises
        ]

        existing_results = []

        if session_exercise_ids:
            response = (
                get_supabase()
                .table("strength_player_results")
                .select("*")
                .eq("player_id", player_id)
                .in_(
                    "session_exercise_id",
                    session_exercise_ids,
                )
                .execute()
            )

            existing_results = response.data or []

        results_by_exercise = {
            result["session_exercise_id"]: result
            for result in existing_results
        }

        result_rows = []

        for exercise in session_exercises:
            existing_result = results_by_exercise.get(
                exercise["id"],
                {},
            )

            result_rows.append(
                {
                    "session_exercise_id": exercise["id"],
                    "Exercice": exercise["exercise_name"],
                    "Séries": exercise["sets_count"],
                    "Répétitions": exercise["reps_count"],
                    "Charge (kg)": existing_result.get(
                        "load_kg",
                        0.0,
                    ),
                    "RPE": existing_result.get(
                        "rpe",
                        0.0,
                    ),
                }
            )

        if not result_rows:
            st.info(
                "Aucun exercice n'est associé à cette séance."
            )

        else:
            results_dataframe = pd.DataFrame(
                result_rows
            )

            edited_results = st.data_editor(
                results_dataframe,
                hide_index=True,
                use_container_width=True,
                disabled=[
                    "session_exercise_id",
                    "Exercice",
                    "Séries",
                    "Répétitions",
                ],
                column_config={
                    "session_exercise_id": None,
                    "Charge (kg)": (
                        st.column_config.NumberColumn(
                            "Charge (kg)",
                            min_value=0.0,
                            step=0.5,
                        )
                    ),
                    "RPE": (
                        st.column_config.NumberColumn(
                            "RPE",
                            min_value=0.0,
                            max_value=10.0,
                            step=0.5,
                        )
                    ),
                },
            )

            save_results = st.button(
                "Enregistrer les résultats",
                type="primary",
                use_container_width=True,
            )

            if save_results:
                result_payloads = []

                for row in edited_results.to_dict(
                    "records"
                ):
                    load_kg = float(
                        row["Charge (kg)"] or 0
                    )

                    repetitions = int(
                        row["Répétitions"]
                    )

                    rpe = float(
                        row["RPE"] or 0
                    )

                    result_payloads.append(
                        {
                            "player_id": player_id,
                            "session_exercise_id": (
                                row[
                                    "session_exercise_id"
                                ]
                            ),
                            "load_kg": load_kg,
                            "rpe": rpe,
                            "estimated_1rm": estimated_1rm(
                                load_kg,
                                repetitions,
                            ),
                        }
                    )

                upsert_rows(
                    "strength_player_results",
                    result_payloads,
                    on_conflict=(
                        "player_id,"
                        "session_exercise_id"
                    ),
                )

                st.success(
                    "Résultats enregistrés."
                )


# -------------------------------------------------------------------
# Historique
# -------------------------------------------------------------------
with tab_history:
    history_results = fetch_all(
        "strength_player_results",
        order="created_at",
        desc=True,
    )

    if not history_results:
        st.info("Aucun résultat.")

    else:
        player_names = {
            player["id"]: player_label(player)
            for player in players
        }

        history_rows = []

        for result in history_results:
            history_rows.append(
                {
                    "Joueur": player_names.get(
                        result.get("player_id"),
                        "Joueur archivé",
                    ),
                    "Charge (kg)": result.get(
                        "load_kg",
                    ),
                    "RPE": result.get(
                        "rpe",
                    ),
                    "1RM estimé": result.get(
                        "estimated_1rm",
                    ),
                    "Date de saisie": result.get(
                        "created_at",
                    ),
                }
            )

        history_dataframe = pd.DataFrame(
            history_rows
        )

        _ = st.dataframe(
            history_dataframe,
            hide_index=True,
            use_container_width=True,
        )