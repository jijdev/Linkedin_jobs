-- ====================================
-- Étape 1 : Création de la base de données et du schéma
-- ====================================

-- Création (ou remplacement) de la base de données "linkedin"
CREATE OR REPLACE DATABASE linkedin;

-- Utilisation de la base "linkedin"
USE DATABASE linkedin;

-- Création (ou remplacement) du schéma "raw" dans la base "linkedin"
CREATE OR REPLACE SCHEMA raw;

-- Utilisation du schéma "raw"
USE SCHEMA raw;

-- ====================================
-- Étape 2 : Définition du stage et des formats de fichiers
-- ====================================

-- Création d’un stage externe pointant vers un bucket S3 public
CREATE OR REPLACE STAGE linkedin_stage
URL='s3://snowflake-lab-bucket/';

-- Définition d’un format de fichier CSV personnalisé
CREATE OR REPLACE FILE FORMAT csv_format 
  TYPE = 'CSV' 
  SKIP_HEADER = 1                       -- Ignore la première ligne (en-tête)
  FIELD_OPTIONALLY_ENCLOSED_BY = '"';  -- Gère les champs entre guillemets

-- Définition d’un format de fichier JSON (utilisé pour certaines tables)
CREATE OR REPLACE FILE FORMAT json_format
  TYPE = 'JSON';

-- ====================================
-- Étape 3 : Création des tables dans le schéma "raw"
-- ====================================

-- Table principale contenant les offres d’emploi
CREATE OR REPLACE TABLE job_postings (
  job_id STRING,
  company_name STRING,
  title STRING,
  description STRING,
  max_salary FLOAT,
  pay_period STRING,
  formatted_work_type STRING,
  location STRING,
  applies STRING,
  original_listed_time STRING,
  remote_allowed FLOAT,
  views INT,
  job_posting_url STRING,
  application_url STRING,
  application_type STRING,
  expiry STRING,
  closed_time STRING,
  formatted_experience_level STRING,
  skills_desc STRING,
  listed_time STRING,
  posting_domain STRING,
  sponsored BOOLEAN,
  work_type STRING,
  currency STRING,
  compensation_type STRING
);

-- ====================================
-- Étape 4 : Chargement des données dans les tables
-- ====================================

-- Chargement des données dans la table "job_postings" depuis un fichier CSV
COPY INTO job_postings
  FROM @linkedin_stage/job_postings.csv
  FILE_FORMAT = (
    TYPE = 'CSV',
    SKIP_HEADER = 0,  -- Ne saute pas de ligne (car PARSE_HEADER est TRUE)
    FIELD_OPTIONALLY_ENCLOSED_BY = '"',
    PARSE_HEADER = TRUE,  -- Utilise la première ligne comme noms de colonnes
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE  -- Ignore les erreurs de colonnes en trop
  )
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;  -- Ignore la casse des noms de colonnes

-- Vérification du chargement
SELECT * FROM job_postings;

-- ===============================
-- Création et chargement des tables additionnelles
-- ===============================

-- Table des avantages sociaux associés aux offres
CREATE OR REPLACE TABLE benefits (
  job_id STRING,
  inferred BOOLEAN,
  type STRING
);



-- Table des données d’effectifs par entreprise
CREATE OR REPLACE TABLE employee_counts (
  company_id STRING,
  employee_count INT,
  follower_count INT,
  time_recorded NUMBER
);

-- Table des compétences associées aux offres
CREATE OR REPLACE TABLE job_skills (
  job_id STRING,
  skill_abr STRING
);

-- Table des industries associées aux offres
CREATE OR REPLACE TABLE job_industries (
  job_id STRING,
  industry_id STRING
);


-- Chargement des données dans les tables additionnelles

-- Avantages (CSV)
COPY INTO benefits
FROM @linkedin_stage/benefits.csv
FILE_FORMAT = (FORMAT_NAME = csv_format);
SELECT * FROM benefits;


-- Effectifs (CSV)
COPY INTO employee_counts
FROM @linkedin_stage/employee_counts.csv
FILE_FORMAT = (FORMAT_NAME = csv_format);

-- Compétences (CSV)
COPY INTO job_skills
FROM @linkedin_stage/job_skills.csv
FILE_FORMAT = (FORMAT_NAME = csv_format);





-- 1️⃣ Création des tables “raw” VARIANT
CREATE OR REPLACE TABLE companies_json             (data VARIANT);
CREATE OR REPLACE TABLE company_industries_json    (data VARIANT);
CREATE OR REPLACE TABLE company_specialities_json  (data VARIANT);
CREATE OR REPLACE TABLE job_industries_json        (data VARIANT);

-- 2️⃣ Chargement brut des JSON dans ces tables
COPY INTO companies_json
  FROM @linkedin_stage/companies.json
  FILE_FORMAT = (FORMAT_NAME = json_format)
  ON_ERROR = 'CONTINUE';

COPY INTO company_industries_json
  FROM @linkedin_stage/company_industries.json
  FILE_FORMAT = (FORMAT_NAME = json_format)
  ON_ERROR = 'CONTINUE';

COPY INTO company_specialities_json
  FROM @linkedin_stage/company_specialities.json
  FILE_FORMAT = (FORMAT_NAME = json_format)
  ON_ERROR = 'CONTINUE';

COPY INTO job_industries_json
  FROM @linkedin_stage/job_industries.json
  FILE_FORMAT = (FORMAT_NAME = json_format)
  ON_ERROR = 'CONTINUE';


-- 3️⃣ Extraction dans vos tables “propres”

-- Table companies déjà présentée :
CREATE OR REPLACE TABLE companies AS
SELECT
    value:company_id::STRING    AS company_id,
    value:name::STRING          AS name,
    value:description::STRING   AS description,
    value:company_size::INT     AS company_size,
    value:state::STRING         AS state,
    value:country::STRING       AS country,
    value:city::STRING          AS city,
    value:zip_code::STRING      AS zip_code,
    value:address::STRING       AS address,
    value:url::STRING           AS url
FROM companies_json,
LATERAL FLATTEN(input => data);

-- Table company_industries
CREATE OR REPLACE TABLE company_industries AS
SELECT
    value:company_id::STRING AS company_id,
    value:industry::STRING   AS industry
FROM company_industries_json,
LATERAL FLATTEN(input => data);

-- Table company_specialities
CREATE OR REPLACE TABLE company_specialities AS
SELECT
    value:company_id::STRING AS company_id,
    value:speciality::STRING AS speciality
FROM company_specialities_json,
LATERAL FLATTEN(input => data);

-- Table job_industries
CREATE OR REPLACE TABLE job_industries AS
SELECT
    value:job_id::STRING      AS job_id,
    value:industry_id::STRING AS industry_id
FROM job_industries_json,
LATERAL FLATTEN(input => data);

--select * from job_industries
CREATE OR REPLACE TABLE industries (
  industry_id STRING,
  industry_name STRING
);

INSERT INTO industries (industry_id, industry_name)
VALUES
  ('IND001', 'Technologie'),
  ('IND002', 'Santé'),
  ('IND003', 'Finance'),
  ('IND004', 'Éducation'),
  ('IND005', 'Commerce de détail'),
  ('IND006', 'Construction'),
  ('IND007', 'Transport'),
  ('IND008', 'Services juridiques'),
  ('IND009', 'Médias'),
  ('IND010', 'Énergie');