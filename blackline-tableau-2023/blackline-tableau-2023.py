import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame
import boto3


def sparkSqlQuery(glueContext, query, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql(query)
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)


args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

client = boto3.client('s3')
bucket_name = 'einc-poc-data-dev'
folder_name = 'blackline'
new_filename = 'blackline_single.csv'

# clean up the folder
def delete_all_files_in_blackline_folder():
    
    s3_folder_path = folder_name+"/"

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    # Iterate over all objects in the "blackline" folder and delete them
    for obj in bucket.objects.filter(Prefix=s3_folder_path):
        obj.delete()

    print(f"All files under {s3_folder_path} in {bucket_name} have been deleted.")
    
delete_all_files_in_blackline_folder()

# Script generated for node Blackline
Blackline_node1 = glueContext.create_dynamic_frame.from_catalog(
    database="data_warehouse",
    table_name="data_warehouse_tableau_vw_office_operation",
    transformation_ctx="Blackline_node1",
    redshift_tmp_dir="s3://einc-poc-data-dev/demo/tmp/",
)

# Script generated for node SQL Query
SqlQuery19 = """
Select Auction_item_id, auction_item_status, purchase_price, transaction_number, transaction_number, sold_date,auction, currency_code, buy_fee_credit, buy_sub_total, buyer_total, transport_fee, buyer_assurance_fee_original, seller_assurance_fee_original, sell_arbitration_insurance_fee, sell_fee, buy_fee, buy_psi_fee, vin, seller, buyer, collect_title_task_status, arbitration_zendesk_ticket_id
From myDataSource
where year=2023
And auction_item_status="SOLD"
"""
SQLQuery_node1 = sparkSqlQuery(
    glueContext,
    query=SqlQuery19,
    mapping={"myDataSource": Blackline_node1},
    transformation_ctx="SQLQuery_node1",
).coalesce(1)

# Script generated for node poc
poc_node1 = glueContext.write_dynamic_frame.from_options(
     frame=SQLQuery_node1,
     connection_type="s3",
     format="csv",
     connection_options={"path": "s3://einc-poc-data-dev/blackline/", "partitionKeys": []},
     transformation_ctx="poc_node1",
 )

# rename file then delete the original file 
def rename_file(bucket_name, folder_name, new_filename):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    objects = list(bucket.objects.filter(Prefix=folder_name))
    if len(objects) == 1:
        old_filename = objects[0].key.split('/')[-1]
        obj = s3.Object(bucket_name, folder_name + '/' + old_filename)
        obj.copy_from(CopySource=bucket_name + '/' + folder_name + '/' + old_filename, 
                      Key=folder_name + '/' + new_filename)
        obj.delete()
    else:
        print('Error: there are multiple files in the specified folder.')

rename_file(bucket_name, folder_name, new_filename)

job.commit()
