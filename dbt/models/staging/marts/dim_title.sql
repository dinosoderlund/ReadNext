-- One row per manga or light novel.
-- This is the catalog the app shows: titles, covers, scores and so on.

select
    title_id,
    title,
    title_english,
    title_romaji,
    format,
    status,
    description,
    average_score,
    popularity,
    chapters,
    volumes,
    start_year,
    cover_image_url,
    site_url
from {{ ref('stg_anilist__media') }}