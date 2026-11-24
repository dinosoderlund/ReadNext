-- A title should never be recommended to itself 
-- dbt runs this query and the tests fails if it returns any rows. 

SELECT * 
FROM {{ ref('fct_recommendations') }}
WHERE title_id = recommended_title_id