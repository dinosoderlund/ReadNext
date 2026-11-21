-- One row per title and genre.
-- A title usually has several genres, e.g. Action + Fantasy + Drama.

select
    media.title_id,
    genre.value::string as genre
from {{ ref('stg_anilist__media') }} as media,
    lateral flatten(input => media.genres) as genre