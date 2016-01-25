
import pandas as pd
import pymysql
import re
import sys
import os
import numpy as np

"""
Addison Lee has different payment structure to other suppliers:
AL only pays 7.5% commission (as opposed to 10%)
AL doesn't pay credit card fees
"""

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
            "and t.date_created < " + "'" + to_date + "' " \
            "and (date_scheduled is null or date_scheduled <" + "'" + to_date + "'" + ") " \
            "and t.date_created > " + "'" + from_date + "' " \
            "and (date_scheduled is null or date_scheduled >" + "'" + from_date + "'" + ") " \
            "order by t.id desc;"

df = pd.read_sql(sql_query, con=core)

#delete all that aren't addison lee
df = df[df.supplier == 'Addison Lee']

## Note: All currency in GBP
df['commission_rate'] = 0.075 #commission for Addison Lee
df['commission'] = df['amount_total'] * df['commission_rate']
df['cc_fees'] = 0 #Are 0 for Addison Lee
df['amount_due_supplier'] = df['amount_total'] - df['commission'] - df['cc_fees']

suppliers = list(set(df['supplier'].values))   # list of unique suppliers

#Insert 12 blank columns
df = (pd.concat([df, pd.DataFrame(columns=list('ABCDEFGHIJKLM'))]))

#supplier_trip_uid - take last 6 digits
df['supplier_trip_uid'] = df.supplier_trip_uid.str.split('|',1)
#df['supplier_trip_uid'] = df['supplier_trip_uid'].apply(lambda x: x[-1])

#Get list of id values and turn to integers
id_list = list(df.index.values)
id_list = map(int, id_list)

#If value in date_scheduled then split into two new column of date and time
#else split it in the same way for date_created
 
for i in id_list:
    if pd.notnull(df['date_scheduled'][i]):
        df['time'] = pd.DatetimeIndex(df['date_scheduled']).time
        df['date'] = pd.DatetimeIndex(df['date_scheduled']).date
    elif pd.notnull(df['date_created'][i]):
        df['time'] = pd.DatetimeIndex(df['date_created']).time
        df['date'] = pd.DatetimeIndex(df['date_created']).date
    else:
        df['time'] = np.nan
        df['date'] = np.nan

#Rearrange these columns and drop unnesccesary 
df = df[['id','date','time','supplier','journey',
         'from_zip_code','to_zip_code','A','B','C',
         'D','supplier_trip_uid','E','F','G',
         'H','I','J','amount_total','K',
         'L','commission_rate','commission','amount_due_supplier','state',
         'vehicle_type','M']]

#Rename column headers
df.columns = ['Karhoo Job No.', 'Pick-up Date', 'Pick-up Time', 'Type', 'Journey', 
              'Pick Up', 'Drop 1', 'Drop 2', 'Drop 3', 'Drop 4', 
              'Drop 5', 'Reference (AL J/N)', 'Basic Job Charge (net)','Waiting Time Qty Actual', 'Waiting Time Qty', 
              'Waiting Time', 'Parking','Extras- Other', 'Total', 'AI total Price', 
              'Difference', 'Commission Rate','Comission Charge', 'Total Due', 'Cancelled', 
              'Notes', 'Addlee notes']

# Write to Excel
writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')

df.to_excel(writer, sheet_name='Addison Lee', index=False)

# Do some basic formatting
writer.sheets['Addison Lee'].set_column('A:D', 18)
writer.sheets['Addison Lee'].set_column('E:E', 90)  # journey
writer.sheets['Addison Lee'].set_column('F:AA', 18)

writer.save()
print('Done. Filed saved at', os.getcwd())
