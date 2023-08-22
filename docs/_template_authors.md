# Authors and Contributors

**Authors** are people whose contributions significantly shaped
the state of `{{ project.name }}` at some point in time.

**Additional contributors** are people who contributed non-trivially to this project
in different ways, e.g. by providing smaller fixes and enhancements to the code
and/or documentation.

Of course, this is just a rough overview and categorization.
For a more complete overview of all contributors and contributions,
please inspect the git history of this repository.

## Authors

{% for p in project.authors() %}
{%- set contr_desc = p.contribution or "" -%}
- {{ p.full_name }} (
  [E-Mail](mailto:{{ p.email }}),
  [ORCID]({{ p.orcid }})
  ){{ ": "+contr_desc if contr_desc else "" }}
{% endfor %}

## Additional Contributors

{% for p in project.contributors() %}
{%- set contr_desc = p.contribution or "" -%}
- {{ p.full_name }} (
  [E-Mail](mailto:{{ p.email }}),
  [ORCID]({{ p.orcid }})
  ){{ ": "+contr_desc if contr_desc else "" }}
{% endfor %}

... maybe **[you](https://materials-data-science-and-informatics.github.io/somesy/latest/contributing)**?

