import pandas as pd
import pymysql
import re
import sys
import os

"""
Addison Lee has different payment structure to other suppliers:
AL only pays 7.5% commission (as opposed to 10%)
AL doesn't pay credit card fees
"""

def main():
    # SQL
    core = pymysql.connect(host='db-1.eu-west-1.karhoo.com', user='karhoo_readonly', password='karhoo_readonly_pw')

    date_reg_exp = re.compile('\d{4}[-]\d{2}[-]\d{2}')

    # Date: from_date (inclusive), to_date (exclusive)
    # i.e. if you want trips from June 1st up to and including November 4,
    # put 2015-11-05 as to_date, 2015-06-01 as from_date
    print('Make sure connected to Karhoo VPN')
    print('Please enter start date in format of YYYY-MM-DD.\n'
          'Start date is INCLUSIVE (i.e. if 2015-06-01 is entered, trips on June 1st will be counted)\n')
    from_date = raw_input()
    if not date_reg_exp.match(from_date):
        print('Input date error. Exit.')
        sys.exit(0)

    print('Please enter end date in format of YYYY-MM-DD.\n'
          'End date is EXCLUSIVE (i.e. if 2015-06-01 is entered, last trip possible is May 31st 11.59pm)\n')
    to_date = raw_input()
    if not date_reg_exp.match(to_date):
        print('Input date error. Exit.')
        sys.exit(0)

    output_filename = from_date + 'to' + to_date + 'trips' + '.xlsx'

    # ---Rates:---
    # All suppliers take 10% unless specified in dict below
    COMMISSION_RATES = {'Addison Lee': 0.075}
    REGULAR_COMMISSION = 0.1
    # All suppliers pay CC fee of 1.9% + 20p except for Addison Lee

    sql_query = "select t.id, t.date_created, t.date_scheduled, s.name as supplier, t.supplier_trip_uid, " \
                "concat(ifnull(t.from_address_1, ''), ' -> ', ifnull(t.to_address_1,'')) as journey, " \
                "t.from_zip_code, t.to_zip_code, " \
                "case when t.state = 9 then 'completed' when t.state = 13 then 'completed' when t.state = 4 then 'cancelled' when t.state = 3 then 'declined' else 'N/A' end as state, " \
                "vt.name as vehicle_type, " \
                "concat(ifnull(u.first_name, ''), ' ', ifnull(u.last_name,'')) as passenger, " \
                "t.amount_estimated, t.amount_total " \
                "from core.core_trip as t " \
                "left join core.core_supplier as s on t.supplier_id = s.id " \
                "left join (core.core_user as u, core.core_vehicletypemapping as vtm, core.core_vehicletype as vt) " \
                "on (t.user_id = u.id and t.vehicle_type_mapping_id = vtm.id and vtm.type_id = vt.id) " \
                "where t.supplier_id != 1 " \
                "and t.supplier_id != 15 " \
				"and s.name NOT IN ('Addison Lee', 'The Keen Group') " \
                "and t.date_created < " + "'" + to_date + "' " \
                "and (date_scheduled is null or date_scheduled <" + "'" + to_date + "'" + ") " \
                "and t.date_created > " + "'" + from_date + "' " \
                "and (date_scheduled is null or date_scheduled >" + "'" + from_date + "'" + ") " \
                "order by t.id desc;"

    df = pd.read_sql(sql_query, con=core)

    # Note: All currency in GBP
    df['commission_rate'] = 0.1
    df['commission_rate'] = df['supplier'].apply(lambda x:  COMMISSION_RATES[x]
                                                            if x in COMMISSION_RATES.keys()
                                                            else REGULAR_COMMISSION)
    df['commission'] = df['amount_total'] * df['commission_rate']
    df['cc_fees'] = df['amount_total'] * 0.019 + 0.2
    df.loc[df['supplier'] == 'Addison Lee', 'cc_fees'] = 0 * df.loc[df['supplier'] == 'Addison Lee', 'cc_fees']
    df['amount_due_supplier'] = df['amount_total'] - df['commission'] - df['cc_fees']

    suppliers = list(set(df['supplier'].values))   # list of unique suppliers

    # Write to Excel
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')

    supplier_totals = df[['supplier', 'amount_total', 'commission',
                          'cc_fees', 'amount_due_supplier']].groupby('supplier').sum()
    supplier_totals.to_excel(writer, sheet_name='totals')

    for s in suppliers:
        df_supp = df[df['supplier'] == s]
        ss = s[:30]
        df_supp.to_excel(writer, sheet_name=str(ss), index=False)

    # Do some basic formatting
    writer.sheets['totals'].set_column('A:A', 40)   # supplier
    writer.sheets['totals'].set_column('B:Z', 15)

    for s in suppliers:
        ss = s[:30]
        writer.sheets[ss].set_column('B:C', 18)  # date_created, date_scheduled
        writer.sheets[ss].set_column('F:F', 90)  # journey
        writer.sheets[ss].set_column('K:K', 20)  # passenger

    writer.save()
    print('Done. Filed saved at', os.getcwd())
    
if __name__ == '__main__':
    main()
