from thetaray.api.solution import DataSet, Field, DataType, IngestionMode
from common.libs.features_discovery import get_features_output_fields as active_fields

from common.libs.config.dataset_loader import load_dataset_config
# config = load_dataset_config('customer_monthly.yaml', domain='domestic')

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, BusinessType
from thetaray.api.solution.explainability import (
    Explainability,
    ExplainabilityType,
    ExplainabilityValueType,
    ExplainabilityValueProperties,
    ExplainabilityValuesFilter,
    ExplainabilityValuesFilterType,
    TimeRangeUnit,
)


def customer_monthly_dataset():
    return DataSet(
        identifier="customer_monthly",
        display_name="customer_monthly",
        field_list=[
                    # generic fields
                       Field(identifier="customer_id", display_name="Customer ID", data_type=DataType.STRING),
                       Field(identifier='year_month', display_name='Year_Month', data_type=DataType.TIMESTAMP),
                       Field(identifier='month_offset', display_name='Month Offset', data_type=DataType.LONG),
                    # populational widget fields
                       Field(identifier="pop_avg_sum_trx", display_name="pop_avg_sum_trx", data_type=DataType.DOUBLE),
                       Field(identifier="pop_avg_cnt_trx", display_name="pop_avg_cnt_trx", data_type=DataType.DOUBLE),
                       Field(identifier="pop_dstnct_cust_trx", display_name="pop_dstnct_cust_trx", data_type=DataType.LONG),
                       Field(identifier="pop_avg_cnt_trx_cash", display_name="pop_avg_cnt_trx_cash", data_type=DataType.DOUBLE),
                       Field(identifier="pop_avg_sum_trx_cash", display_name="pop_avg_sum_trx_cash", data_type=DataType.DOUBLE),
                       Field(identifier="pop_dstnct_cust_trx_cash", display_name="pop_dstnct_cust_trx_cash", data_type=DataType.LONG),
                       Field(identifier="pop_avg_cnt_trx_n_day", display_name="pop_avg_cnt_trx_n_day", data_type=DataType.DOUBLE),
                       Field(identifier="pop_avg_new_account", display_name="pop_avg_new_account", data_type=DataType.DOUBLE),
                       Field(identifier="pop_dstnct_cust_new_account", display_name="pop_dstnct_cust_new_account", data_type=DataType.LONG),
                    # categorical widget fields
                       Field(identifier="one_to_many_explainability", display_name="One to Many Explainability", data_type=DataType.STRING, category="One to Many", is_explainability_column=True),
                       Field(identifier="many_to_one_explainability", display_name="Many to One Explainability", data_type=DataType.STRING, category="Many to One", is_explainability_column=True),
                       Field(identifier="high_risk_country_explainability", display_name="High Risk Country Explainability", data_type=DataType.STRING, category="High Risk Country Explainability", is_explainability_column=True),
                       Field(identifier="cp_concentration_explainability", display_name="Concentration Explainability", data_type=DataType.STRING, category="Concentration Explainability", is_explainability_column=True),
                       Field(identifier="sum_trx_fop_explainability", display_name="FOP Explainability", data_type=DataType.STRING, category="FOP Explainability", is_explainability_column=True),
                    # additional features
                       Field(identifier="cp_concentration", 
                             display_name="Counterparty Concentration",
                             data_type=DataType.DOUBLE,
                             category="Transactional",
                             dynamic_description = """
                      Customer **{{ activity.customer_id }}** has sent funds to **{{ activity.one_to_many }}** unique counterparties in the current month, totaling **${{ activity.sum_trx | round(2) }}**. The customer has concentrated **{{ (activity.cp_concentration * 100) | round(0) }}%** to a single counterparty, which corresponds to **${{ activity.cp_concentration_s }}**.
                      """,
                     explainabilities=[
                        Explainability(
                            identifier="categorical_expl",
                            type=ExplainabilityType.CATEGORICAL,
                            category_lbl="cn",
                            category_var="s",
                            json_column_reference="cp_concentration_explainability",
                            values=[
                                ExplainabilityValueProperties(
                                    key="cn",
                                    name="Couterparty Name",
                                ),
                                ExplainabilityValueProperties(
                                    key="s",
                                    name="Sum of Transactions",
                                    type=ExplainabilityValueType.SUM,
                                ),
                                # ExplainabilityValueProperties(
                                #     key="c",
                                #     name="Transaction Count",
                                #     type=ExplainabilityValueType.COUNT,
                                # )
                            ]
                        )
                     ]
                ),
                       Field(identifier="cp_concentration_s", display_name="cp_concentration_s", data_type=DataType.DOUBLE),
                       Field(identifier='sum_in_trx_3d', display_name='Incoming Value 3d', data_type=DataType.DOUBLE),
                       Field(identifier='sum_out_trx_3d', display_name='Outgoing Value 3d', data_type=DataType.DOUBLE),
                       Field(identifier='sum_rapid_movement',
                      display_name='Rapid Movement of Funds',
                      description='High value turnover (i.e. pipe customer activity)',
                      category='Transactional Activity',
                      data_type=DataType.DOUBLE,
                      dynamic_description=
                      """
                      Customer **{{ activity.customer_id }}** received transactions totaling **${{ activity.sum_in_trx_3d | round(2) }}** and sent transactions totaling **${{ activity.sum_out_trx_3d | round(2) }}** in a period of 3 days.

                      This pattern might indicate pipe account behavior.

                      """,
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      explainabilities=[
                          Explainability(
                            identifier="hist_expl",
                            type=ExplainabilityType.HISTORICAL,
                            time_range_value=10,
                            time_range_unit=TimeRangeUnit.MONTH,
                            values=[ExplainabilityValueProperties(
                                        key="zval",
                                        name="Pipe Customer",
                                        dynamic_value="sum_rapid_movement",
                                        type=ExplainabilityValueType.TREND)])])
                   ] + active_fields('demo_fuib', 'customer', 'monthly'),
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['customer_id'],
        data_permission="dpv:demo_fuib",
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field="year_month"
    )


def entities():
    return [customer_monthly_dataset()]
