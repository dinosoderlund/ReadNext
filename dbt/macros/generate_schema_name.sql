-- By default dbt names custom schemas "<target schema>_<custom schema>",
-- e.g. STAGING_MARTS. This macro makes dbt use the name we set as it is,
-- so models land in READNEXT.STAGING and READNEXT.MARTS.

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}