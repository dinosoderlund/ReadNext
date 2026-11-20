-- Turns the raw JSON from AniList into normal columns.
-- One row per manga or light novel.

select
    id                                          as title_id,
    coalesce(
        payload:title:english::string,
        payload:title:romaji::string
    )                                           as title,
    payload:title:english::string               as title_english,
    payload:title:romaji::string                as title_romaji,
    payload:format::string                      as format,
    payload:status::string                      as status,
    payload:description::string                 as description,
    payload:averageScore::number                as average_score,
    payload:popularity::number                  as popularity,
    payload:chapters::number                    as chapters,
    payload:volumes::number                     as volumes,
    payload:startDate:year::number              as start_year,
    payload:coverImage:large::string            as cover_image_url,
    payload:siteUrl::string                     as site_url,
    payload:genres                              as genres,
    payload:tags                                as tags,
    loaded_at

from {{ source('anilist', 'anilist_media') }}