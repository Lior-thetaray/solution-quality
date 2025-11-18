from thetaray.api.solution.summarization import AlertSummarizationType
from thetaray.api.solution.evaluation import AlertConfiguration
from thetaray.common.constants import Constants

def config():
    return AlertConfiguration(llm_summarization=True,
                              summarization_types=[AlertSummarizationType(identifier=Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.identifier,
                                                                        name = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.name,
                                                                        description = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.description,
                                                                        llm_model = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.llm_model,
                                                                        fallback_llm_model=Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.fallback_llm_model,
                                                                        prompt_template="""
    {%- if risk.metadata.analysis_method == "AI" -%}
    Anomalous behavior indicating money laundry activity has been identified for customer-{{ activity.merchant_id }} by a machine learning
    model with a probability of {{ algo.score }}.
    
    The features with high rating, impacting the prediction are -
    {{ algo.features[0].identifier }} with a rating of {{ algo.features[0].rating }}-{{ algo.features[0].description }}
    {{ algo.features[1].identifier }} with a rating of {{ algo.features[1].rating }}-{{ algo.features[1].description }}
    {{ algo.features[2].identifier }} with a rating of {{ algo.features[2].rating }}-{{ algo.features[2].description }}
    
    All Feature values and descriptions -
    {%- for feature in algo.features %}
    {{ feature.identifier }}={{ feature.value }} | {{ feature.name }}
    {%- endfor -%}
    {%- endif %}
    {%- if risk.metadata.analysis_method == "RULE" -%}
    Anomalous behavior indicating money laundering activity has been identified for customer - {{ activity.merchant_id }} by a rule based
    model.
    Rule Details:
        conditions_display: {{ risk.metadata.conditions_display }}
        description: {{ risk.metadata.description }}
        severity: {{ risk.metadata.severity }}
    {%- endif %}
    
    All enrichments values-
    {%- if not risk.enrichments.values() -%}
    No enrichments detected
    {%- else -%}
    {%- for enrichment in risk.enrichments.values() %}
        {{ enrichment.identifier }}-{{ enrichment.value }}
    {%- endfor -%}
    {%- endif %}
    
    All variables values and descriptions-
    {%- for variable in risk.variables.values() %}
        {{ variable.identifier }}-{{ variable.value }}-{{ variable.description }}
    {%- endfor %}
    
    Additional forensic information -
    {%- for forensic in activity.forensic_fields.values() %}
        {{ forensic.identifier }}-{{ forensic.value }}-{{ forensic.description }}
    {%- endfor %}
    
    Please provide a summary in the following format
    - a 2 row textual summary of the alert focusing on the customer details and reason for alerting
    - the list of features with rating provided by the algorithm. The information should include feature name, description, value and rating. The information should be presented as bulleted rows
    - additional information the is associated with suspicious activity within up to 5 rows. Don't repeat information that is included in the features with high rating
    The output should be limited to 10 rows and be formatted using markdown
    probability should be indicated in percentage
    """
)])