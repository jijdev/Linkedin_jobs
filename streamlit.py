import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark import Session
import os
from snowflake.snowpark import Session
import os
from dotenv import load_dotenv

load_dotenv()  # Charge les variables d’environnement

connection_parameters = {
    "account": "OMB26827.us-west-2",  # 🔁 adapte selon ton compte
    "user": "hagar",
    "password": "7B7XPjqjVP2ksgu",
    "role": "ACCOUNTADMIN",
    "warehouse": "COMPUTE_WH",
    "database": "LINKEDIN",
    "schema": "RAW"
}

# ⸻ Session Snowpark

session = Session.builder.configs(connection_parameters).create()

# ⸻ Fonction de requête avec cache
@st.cache_data(ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    df = session.sql(sql).to_pandas()
    df.columns = df.columns.str.lower()
    return df

st.title("📊 Dashboard LinkedIn Job Postings")

# ─────────────────────────────────────────────────────────────────────────────
# KPI 1 : Top 10 des titres les plus publiés → Bubble chart
# ─────────────────────────────────────────────────────────────────────────────
st.header("1️⃣ Top 10 des titres les plus publiés (avec industrie)")
q1 = """
WITH counts AS (
  SELECT jp.title AS title,
         ji.industry_id AS industry,
         COUNT(*) AS cnt
    FROM raw.job_postings jp
    JOIN raw.job_industries ji ON jp.job_id = ji.job_id
   GROUP BY jp.title, ji.industry_id
)
SELECT title, industry, cnt
  FROM counts
 ORDER BY cnt DESC
 LIMIT 10
"""
with st.spinner("🔄 Chargement KPI 1…"):
    df1 = run_query(q1)

if df1.empty:
    st.warning("⚠️ Pas de données pour le KPI 1")
else:
    df1["cnt"] = pd.to_numeric(df1["cnt"], errors="coerce").fillna(0)
    chart1 = (
        alt.Chart(df1)
        .mark_circle(opacity=0.7)
        .encode(
            x=alt.X("cnt:Q", title="Nombre d'offres"),
            y=alt.Y("title:N", sort="-x", title="Titre de poste"),
            size=alt.Size("cnt:Q",
                          scale=alt.Scale(range=[100, 1000]),
                          title="Volume d'offres"),
            color=alt.Color("industry:N", title="Industrie"),
            tooltip=["title", "industry", "cnt"]
        )
        .properties(width=700, height=400)
        .interactive()
    )
    st.altair_chart(chart1, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI 2 → Heatmap (titre × industrie by salaire moyen)
# ─────────────────────────────────────────────────────────────────────────────
st.header("2️⃣ Top 10 des postes les mieux rémunérés (avec industrie)")
q2 = """
WITH salaries AS (
  SELECT jp.title          AS title,
         ji.industry_id    AS industry,
         AVG(jp.max_salary) AS avg_salary
    FROM raw.job_postings jp
    JOIN raw.job_industries ji ON jp.job_id = ji.job_id
   WHERE jp.max_salary IS NOT NULL
   GROUP BY jp.title, ji.industry_id
)
SELECT title, industry, avg_salary
  FROM salaries
 ORDER BY avg_salary DESC
 LIMIT 10
"""
df2 = run_query(q2)
if df2.empty:
    st.warning("⚠️ Pas de données pour le KPI 2")
else:
    df2["avg_salary"] = df2["avg_salary"].astype(float)
    chart2 = (
        alt.Chart(df2)
        .mark_rect()
        .encode(
            y=alt.Y("title:N", sort="-x", title="Titre de poste"),
            x=alt.X("industry:N",            title="Industrie"),
            color=alt.Color("avg_salary:Q",
                            scale=alt.Scale(scheme="blues"),
                            title="Salaire moyen"),
            tooltip=[
                alt.Tooltip("title:N",      title="Titre"),
                alt.Tooltip("industry:N",   title="Industrie"),
                alt.Tooltip("avg_salary:Q", format=",.0f", title="Salaire moyen")
            ]
        )
        .properties(width=700, height=400)
    )
    st.altair_chart(chart2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI 3 → KPI 3 → Line chart
# ─────────────────────────────────────────────────────────────────────────────
st.header("3️⃣ Répartition des offres d’emploi par taille d’entreprise")
q3 = """
SELECT ec.employee_count AS employee_count,
       COUNT(jp.job_id)   AS postings_count
  FROM raw.employee_counts ec
  LEFT JOIN raw.companies c
    ON ec.company_id = c.company_id
  LEFT JOIN raw.job_postings jp
    ON LOWER(TRIM(jp.company_name)) = LOWER(TRIM(c.name))
 GROUP BY ec.employee_count
 ORDER BY ec.employee_count
"""
with st.spinner("🔄 Chargement KPI 3…"):
    df3 = run_query(q3)
if df3.empty:
    st.warning("⚠️ Pas de données pour le KPI 3")
else:
    df3["employee_count"] = pd.to_numeric(df3["employee_count"], errors="coerce")
    df3["postings_count"]  = pd.to_numeric(df3["postings_count"], errors="coerce")
    chart3 = (
        alt.Chart(df3)
        .mark_line(point=True, color="#1f77b4")
        .encode(
            x=alt.X("employee_count:Q", title="Nombre d'employés"),
            y=alt.Y("postings_count:Q", title="Nombre d'offres"),
            tooltip=["employee_count", "postings_count"]
        )
        .properties(width=700, height=350)
        .interactive()
    )
    st.altair_chart(chart3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI 4 & 5 côte-à-côte → Bar chart & Donut chart
# ─────────────────────────────────────────────────────────────────────────────
col4, col5 = st.columns(2)

with col4:
    st.header("4️⃣ Répartition des offres d’emploi par secteur d’activité")
    q4 = """
    SELECT ji.industry_id AS industry,
           COUNT(*)        AS cnt
      FROM raw.job_postings jp
      JOIN raw.job_industries ji ON jp.job_id = ji.job_id
     GROUP BY ji.industry_id
     ORDER BY cnt DESC
    """
    df4 = run_query(q4)
    if df4.empty:
        st.warning("⚠️ Pas de données pour le KPI 4")
    else:
        df4["cnt"] = df4["cnt"].astype(int)
        base4 = (
            alt.Chart(df4)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                y=alt.Y("industry:N", sort="-x", title="Secteur"),
                x=alt.X("cnt:Q", title="Nombre d'offres"),
                color=alt.Color("cnt:Q",
                                scale=alt.Scale(scheme="oranges"),
                                legend=None),
                tooltip=["industry", "cnt"]
            )
            .properties(width=350, height=350)
        )
        labels4 = base4.mark_text(
            align="left", dx=3, dy=0, fontSize=12, color="black"
        ).encode(text="cnt:Q")
        st.altair_chart(base4 + labels4, use_container_width=True)

with col5:
    st.header("5️⃣ Répartition des offres d’emploi par type d’emploi (temps plein, stage, temps partiel)")
    q5 = """
    SELECT formatted_work_type AS work_type,
           COUNT(*)            AS cnt
      FROM raw.job_postings
     GROUP BY formatted_work_type
     ORDER BY cnt DESC
    """
    df5 = run_query(q5)
    if df5.empty:
        st.warning("⚠️ Pas de données pour le KPI 5")
    else:
        df5["cnt"] = df5["cnt"].astype(int)
        base5 = (
            alt.Chart(df5)
            .encode(
                theta=alt.Theta("cnt:Q", title="Nombre d'offres"),
                color=alt.Color("work_type:N",
                                scale=alt.Scale(scheme=COLOR_SCHEME),
                                title="Type d’emploi"),
                tooltip=["work_type", "cnt"]
            )
        )
        chart5 = base5.mark_arc(innerRadius=50, outerRadius=100)
        total = df5["cnt"].sum()
        center_text = alt.Chart(
            pd.DataFrame({"text":[f"Total\n{total}"]})
        ).mark_text(size=16, fontWeight="bold").encode(text="text:N")
        st.altair_chart(
            (chart5 + center_text).properties(width=350, height=350),
            use_container_width=True
        )
