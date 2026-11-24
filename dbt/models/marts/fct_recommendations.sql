-- for every title: the 10 most similar titles, based on shared tags 

/*
    1. Every tag gets a weight from 0 to 1 (tag_rank / 100).
       "Isekai" with rank 95 counts more than "Magic" with rank 40. 
    2. Two titles get points for every tag they share: weight_a * weight_b.
    3. The points are divided by each title's total tag weight,
       so titles with many tags don't win just because they have many tags.
       The score ends up between 0 and 1.
    4. The best 10 matches per title, plus the 3 strongest shared tags are kept
       so the app can also explain why
*/

with tags as(

    select title_id, tag_name, tag_rank / 100 as weight
    from {{ ref('bridge_title_tag') }}
    where tag_rank >= 50
),

title_lengths as(

    select title_id, sqrt(sum(weight * weight)) as length
    from tags 
    group by title_id

),

shared_tags as(
    select a.title_id, b.title_id as recommended_title_id, a.tag_name, a.weight * b.weight as points
    from tags as a
    inner join tags as b
    on a.tag_name = b.tag_name
    and a.title_id <> b.title_id  

),

scores as(
    select shared.title_id, shared.recommended_title_id, sum(shared.points) / (len_a.length * len_b.length) as similarity_score,
    count(*) as shared_tag_count, array_slice(array_agg(shared.tag_name) within group (order by shared.points desc), 0, 3)   as top_shared_tags
    from shared_tags as shared
    inner join title_lengths as len_a on shared.title_id = len_a.title_id
    inner join title_lengths as len_b on shared.recommended_title_id = len_b.title_id
    group by shared.title_id, shared.recommended_title_id, len_a.length, len_b.length

)


select scores.title_id, scores.recommended_title_id,
row_number() over (partition by scores.title_id order by scores.similarity_score desc, recommended.popularity desc) as recommendation_rank,
round(scores.similarity_score, 3) as similarity_score,
scores.shared_tag_count, scores.top_shared_tags
from scores
inner join {{ ref('dim_title') }} as recommended
on scores.recommended_title_id = recommended.title_id
qualify recommendation_rank <= 10