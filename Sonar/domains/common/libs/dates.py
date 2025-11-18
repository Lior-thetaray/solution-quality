from pyspark.sql.types import TimestampType, LongType, IntegerType
from pyspark.sql import functions as F
from thetaray.common.constants import Constants
from datetime import datetime

class Consts:
    MONTH_OFFSET_PREFIX = 'month_offset_'
    WEEK_OFFSET_PREFIX = 'week_offset_'
    DAY_OFFSET_PREFIX = 'day_offset_'
    MONTH = 'month'
    WEEK = 'week'
    DAY = 'day'
    BEGINNING_OF_MONDAYS = datetime(1970, 1, 5)
    END_OF_TIME = datetime(2099, 1, 1)


days_to_seconds = lambda ndays: ndays*60*60*24


def add_month_offset_column(df, date_column_name, output_column_name=None):
    """
    Add a column that specifies the relative month, in integers, to the to BEGINNING OF TIME (1/1/1970)

    Parameters
    ----------
    df: DataFrame
        The dataframe to compute month_offset_fore
    date_column_name: str
        The name of the date column
    output_column_name: str
        The name of the column to hold the output

    Returns
    -------
    DataFrame
        Same dataframe with an additional offset column counted from BEGINNING OF TIME (1/1/1970)
    """
    new_column_name = output_column_name or f'{Consts.MONTH_OFFSET_PREFIX}{date_column_name}'
    df = df.withColumn(new_column_name, F.round(F.months_between(F.trunc(F.col(date_column_name), Consts.MONTH), F.lit(Constants.BEGINNING_OF_TIME))).cast(LongType()))
    return df

def add_day_offset_column(df, date_column_name, output_column_name=None):
    """
    Add a column that specifies the relative day, in integers, to the to BEGINNING OF TIME (1/1/1970)

    Parameters
    ----------
    df: DataFrame
        The dataframe to compute day_offset_fore
    date_column_name: str
        The name of the date column
    output_column_name: str
        The name of the column to hold the output

    Returns
    -------
    DataFrame
        Same dataframe with an additional offset column counted from BEGINNING OF TIME (1/1/1970)
    """
    new_column_name = output_column_name or f'{Consts.DAY_OFFSET_PREFIX}{date_column_name}'
    df = df.withColumn(new_column_name, F.datediff(F.col(date_column_name), F.lit(Constants.BEGINNING_OF_TIME)).cast(LongType()))
    return df
                       
def add_week_offset_column(df, date_column_name, output_column_name=None):
    """
    Add a column that specifies the relative week, in integers, to the to BEGINNING OF MONDAYS (5/1/1970)

    Parameters
    ----------
    df: DataFrame
        The dataframe to compute week_offset_fore
    date_column_name: str
        The name of the date column
    output_column_name: str
        The name of the column to hold the output

    Returns
    -------
    DataFrame
        Same dataframe with an additional offset column counted from BEGINNING OF MONDAYS (5/1/1970)
    """
    new_column_name = output_column_name or f'{Consts.WEEK_OFFSET_PREFIX}{date_column_name}'
    df = df.withColumn(new_column_name, F.floor(F.datediff(F.col(date_column_name), F.lit(Consts.BEGINNING_OF_MONDAYS))/7).cast(LongType()))
    return df


def month_offset_to_year_month_columns(df, month_offset_column_name, output_column_name):
    """Add a column with the date of the first day in that month, based on a pre-calculated month_offset column

    Parameters
    ----------
    df: DataFrame
        The dataframe containing the date column
    month_offset_column_name: str
        The name of the column containing a number indicating the number of months passed since January 1970

    Returns
    -------
    DataFrame
        Same df with the additional column
    """
    
    df = df.withColumn(output_column_name, F.expr(f'add_months("{Constants.BEGINNING_OF_TIME.date()}", {month_offset_column_name})').cast(TimestampType()))    
    return df


def week_offset_to_first_monday_columns(df, week_offset_column_name, output_column_name):
    """Add a column with the date of the first day in that week, based on a pre-calculated week_offset column

    Parameters
    ----------
    df: DataFrame
        The dataframe containing the date column
    week_offset_column_name: str
        The name of the column containing a number indicating the number of weeks passed since January 5th 1970

    Returns
    -------
    DataFrame
        Same df with the additional column
    """
    
    df = df.withColumn('add_days_to_monday', (F.col(week_offset_column_name)*7).cast(IntegerType()))
    df = df.withColumn(output_column_name, (F.expr(f'date_add("{Consts.BEGINNING_OF_MONDAYS}",add_days_to_monday)')).cast(TimestampType())) 
    return df.drop('add_days_to_monday')

def day_offset_to_date_columns(df, day_offset_column_name, output_column_name):
    """Add a column with the date, based on a pre-calculated day_offset column

    Parameters
    ----------
    df: DataFrame
        The dataframe containing the date column
    day_offset_column_name: str
        The name of the column containing a number indicating the number of days passed since January 1st 1970

    Returns
    -------
    DataFrame
        Same df with the additional columns
    """
    
    df = df.withColumn('int_offset',F.col(day_offset_column_name).cast(IntegerType())) 
    df = df.withColumn(output_column_name, F.expr(f'date_add("{Constants.BEGINNING_OF_TIME.date()}", int_offset)').cast(TimestampType())) 
    return df.drop('int_offset')





