from thetaray.api.solution import (CustomerInsights, InsightField, InsightFieldType, InsightPeriod, InsightType, InsightWidget)


def config():
    return CustomerInsights(
            dataset="demo_ret_indiv_customer_insights",
            widgets=[
                InsightWidget(
                    identifier="kyc",
                    display_name="KYC Widget",
                    type=InsightType.KYC,
                    fields=[
                        InsightField(
                            field_ref="kyc_classification",
                            type=InsightFieldType.CLASSIFICATION,
                        ),
                        InsightField(
                            field_ref="kyc_name", type=InsightFieldType.CUSTOMER_NAME
                        ),
                        InsightField(
                            field_ref="kyc_is_new", type=InsightFieldType.TAG
                        ),
                        InsightField(
                            field_ref="kyc_recently_updated",
                            type=InsightFieldType.TAG,
                        ),
                        InsightField(
                            field_ref="kyc_newly_incorporation",
                            type=InsightFieldType.TAG,
                        ),
                        InsightField(
                            field_ref="kyc_new_customer",
                            type=InsightFieldType.TAG,
                        ),
                        InsightField(
                            field_ref="kyc_occupation",
                        ),
                        InsightField(
                            field_ref="kyc_null_field",
                        ),
                    ],
                ),
                InsightWidget(
                    identifier="ga",
                    display_name="Geographical Activity Widget",
                    type=InsightType.GEOGRAPHICAL_ACTIVITY,
                    fields=[
                        InsightField(
                            field_ref="hr_cc", type=InsightFieldType.HIGH_RISK_COUNTRIES
                        ),
                        InsightField(
                            field_ref="mr_cc",
                            type=InsightFieldType.MEDIUM_RISK_COUNTRIES,
                        ),
                        InsightField(
                            field_ref="lr_cc", type=InsightFieldType.LOW_RISK_COUNTRIES
                        ),
                        InsightField(
                            field_ref="director_ad", type=InsightFieldType.ADDRESS
                        ),
                        InsightField(
                            field_ref="company_ad", type=InsightFieldType.ADDRESS
                        ),
                    ],
                ),
                InsightWidget(
                    identifier="tr",
                    display_name="Transactional Activity Widget",
                    type=InsightType.CUSTOMER_ACTIVITY,
                    fields=[
                        InsightField(field_ref="tr_in", type=InsightFieldType.TRX_IN),
                        InsightField(field_ref="tr_out", type=InsightFieldType.TRX_OUT),
                        InsightField(
                            field_ref="tr_in_count", type=InsightFieldType.TRX_IN_DETAIL
                        ),
                        InsightField(
                            field_ref="tr_out_count",
                            type=InsightFieldType.TRX_OUT_DETAIL,
                        ),
                        InsightField(
                            field_ref="tr_in_seg",
                            type=InsightFieldType.TRX_POPULATION_IN,
                        ),
                        InsightField(
                            field_ref="tr_out_seg",
                            type=InsightFieldType.TRX_POPULATION_OUT,
                        ),
                        InsightField(
                            field_ref="tr_in_seg_count",
                            type=InsightFieldType.TRX_POPULATION_IN_DETAIL,
                        ),
                        InsightField(
                            field_ref="tr_out_seg_count",
                            type=InsightFieldType.TRX_POPULATION_OUT_DETAIL,
                        ),
                    ],
                    period=InsightPeriod(
                        from_ref="trx_from_date",
                        to_ref="trx_to_date"
                    )
                ),
                InsightWidget(
                    identifier="alerts",
                    display_name="Historical Alerts Widget",
                    type=InsightType.HISTORICAL_ALERTS,
                    fields=[
                        InsightField(field_ref="tm", type=InsightFieldType.CATEGORY),
                        InsightField(field_ref="scrn", type=InsightFieldType.CATEGORY),
                    ],
                    period=InsightPeriod(
                        from_ref="trx_from_date",
                        to_ref="trx_to_date"
                    )
                ),
            ],
        )