-- One row per title and tag.
-- Tags are more detailed than genres (e.g. "Isekai", "Found Family").
-- tag_rank (0-100) says how strongly the tag fits the title.

select
    media.title_id,
    tag.value:name::string as tag_name,
    tag.value:rank::number as tag_rank
from {{ ref('stg_anilist__media') }} as media,
    lateral flatten(input => media.tags) as tag