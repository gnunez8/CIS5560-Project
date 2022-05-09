# -*- coding: utf-8 -*-
"""UCMasterFull.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1bGgta4xLPVpaG6X4bU-6LOMG0HGooV7A
"""

# COMMAND ---
from pyspark.sql.types import *
from pyspark.sql.functions import *

from pyspark.ml import *
from pyspark.ml.regression import LinearRegression , DecisionTreeRegressor, RandomForestRegressor, GBTRegressionModel, GBTRegressor

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.tuning import ParamGridBuilder, TrainValidationSplit, CrossValidator
from pyspark.ml.evaluation import RegressionEvaluator

from pyspark.ml.feature import VectorIndexer
from pyspark.ml.feature import VectorAssembler, MinMaxScaler
from pyspark.ml.linalg import Vectors

from pyspark.ml.evaluation import BinaryClassificationEvaluator

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from pyspark.context import SparkContext
from pyspark.mllib.evaluation import MulticlassMetrics
from pyspark.sql.session import SparkSession

# COMMAND ---
PYSPARK_CLI = True
if PYSPARK_CLI:
	sc = SparkContext.getOrCreate()
	spark = SparkSession(sc)

# COMMAND ---
# File location and type
#file_location = "/FileStore/tables/2016_UniversityOfCalifornia.csv"
file_location = "/user/jdang8/2016_UniversityOfCalifornia.csv"
file_type = "csv"

# CSV options
infer_schema = "true"
first_row_is_header = "true"
delimiter = ","

# The applied options are for CSV files. For other file types, these will be ignored.
df = spark.read.format(file_type).option("inferSchema", infer_schema)\
  .option("header", first_row_is_header) \
  .option("sep", delimiter) \
  .load(file_location)

print("Table 2016_UniversityOfCalifornia")
df.show()

# COMMAND ---
df.printSchema()

# Create a view or table

temp_table_name = "2016_UniversityOfCalifornia_csv"

df.createOrReplaceTempView(temp_table_name)

dftemp=df.select('EmployerName','Position','TotalWages', 'RegularPay', 'MaxPositionSalary', 'MinPositionSalary')
#dftemp.show()

# Commented out IPython magic to ensure Python compatibility.
# %sql
#select * from `2016_UniversityOfCalifornia_csv`

#df.take(10)

#df_sql = spark.sql("select * from 2016_UniversityOfCalifornia_csv LIMIT 10")
#display(df_sql)

#df.printSchema()

df2 = df.drop("DepartmentOrSubdivision", "ElectedOfficial", "Judicial","OtherPositions", "DefinedBenefitPlanContribution","EmployeesRetirementCostCovered", "DeferredCompensationPlan","HealthDentalVision", "TotalRetirementAndHealthContribution","PensionFormula", "EmployerURL","EmployerPopulation","IncludesUnfundedLiability", "SpecialDistrictActivities"," IncludesUnfundedLiability","SpecialDistrictType")
#df2.printSchema()

print("Table 2016_UniversityOfCalifornia with Dropped Columns")
#df2.show()

# COMMAND ---
df3 = df2.na.fill(value=0).na.fill("NA")
print("Table 2016_UniversityOfCalifornia with Dropped Columns")
df3.show()

# COMMAND ---
splits = df3.randomSplit([0.7,0.3])
train = splits[0]
test = splits[1]
train_rows = train.count()
test_rows = test.count()
print("Training Rows:", train_rows, "Testing Rows:", test_rows)

# COMMAND ---
assembler = VectorAssembler(inputCols = ["RegularPay", "TotalWages","MaxPositionSalary", "MinPositionSalary"], outputCol="wages")

# COMMAND ---
training = assembler.transform(train)
print("Displaying results from Training the dataset")
training.show()

# COMMAND ---
rf = RandomForestRegressor(labelCol="TotalWages", featuresCol="wages", numTrees=10, maxDepth=5)

# COMMAND ---
pipeline = Pipeline(stages=[assembler, rf])
print("Displaying results from Staging the Assembler and RF")
model = pipeline.fit(train)

# COMMAND ---
rfModel = model.stages[-1]
print(rfModel.toDebugString)

#importance column name can be changed

# import pandas as pd
#featureImp = pd.DataFrame(list(zip(assembler.getInputCols(),
#rfModel.featureImportances)),
#columns=["trueWages", "importance"])
#featureImp.sort_values(by="importance", ascending=False)

# COMMAND ---
rf = RandomForestRegressor(labelCol="TotalWages",featuresCol="wages", numTrees=10, maxDepth=5)
# Combine stages into pipeline
pipeline = Pipeline(stages=[assembler, rf])
model = pipeline.fit(train)

# COMMAND ---
prediction = model.transform(test)
predicted = prediction.select("wages", "prediction", "TotalWages")
print("Displaying results from the Prediction")
predicted.show()

#display(predicted)
#predicted.show()
#z.show(predicted)

# COMMAND ---
#from pyspark.ml.evaluation import RegressionEvaluator
rf_evaluator = RegressionEvaluator(predictionCol="prediction", \
                                   labelCol="TotalWages",metricName="r2")
print("R Squared (R2) on test data = %g" % rf_evaluator.evaluate(prediction))
rf_evaluator = RegressionEvaluator(labelCol="TotalWages", predictionCol="prediction", metricName="rmse")
print("RMSE: %f" % rf_evaluator.evaluate(prediction))

#Starting GBT

# COMMAND ---
df3 = df2.na.fill(value=0).na.fill("NA")
#df3.show()

# COMMAND ---
splits = df3.randomSplit([0.7,0.3])
train = splits[0]
test = splits[1]
train_rows = train.count()
test_rows = test.count()
print("Training Rows:", train_rows, "Testing Rows:", test_rows)

# COMMAND ---
assembler = VectorAssembler(inputCols = ["RegularPay", "TotalWages","MaxPositionSalary", "MinPositionSalary"], outputCol="wages")

# COMMAND ---
training = assembler.transform(train)
#training.show()

# COMMAND ---

gbt = GBTRegressor(labelCol="TotalWages", featuresCol="wages", maxDepth=5)

# COMMAND ---
paramGrid = ParamGridBuilder()\
.addGrid(gbt.maxDepth, [2, 5])\
.addGrid(gbt.maxIter, [10, 20])\
.build()

# COMMAND ---
#gbt_evaluator = RegressionEvaluator(predictionCol="prediction", \ labelCol="TotalWages",metricName="r2")

gbt_evaluator = RegressionEvaluator(predictionCol="prediction", labelCol="TotalWages", metricName="r2")

# COMMAND ---
pipeline = Pipeline(stages=[assembler, gbt])

# COMMAND ---
cv = CrossValidator(estimator=pipeline, evaluator= gbt_evaluator, estimatorParamMaps=paramGrid)

# COMMAND ---
print("Displaying results from CrossValidation with the trained dataset")
model = cv.fit(train)

# COMMAND ---
#test.show()

# COMMAND ---
prediction = model.transform(test)
predicted = prediction.select("wages", "prediction", "TotalWages")
print("Displaying results from TrainValidationSplit with the Predicted dataset")
predicted.show()

# COMMAND ---
#predicted.show()

# COMMAND ---
print("R Squared (R2) on test data = %g" % gbt_evaluator.evaluate(prediction))
gbt_evaluator = RegressionEvaluator(labelCol="TotalWages", predictionCol="prediction", metricName="rmse")
print("RMSE: %f" % gbt_evaluator.evaluate(prediction))

# COMMAND ---
cva = TrainValidationSplit(estimator= pipeline, evaluator=gbt_evaluator, estimatorParamMaps=paramGrid, trainRatio=0.8)

print("Displaying results from TrainValidationSplit with the trained dataset")
example = cva.fit(train)

# Transform the test data and generate predictions by applying the trained model
prediction = example.transform(test)
predicted = prediction.select("wages", "prediction", "TotalWages")
print("Displaying results from TrainValidationSplit with the Predicted dataset")
predicted.show()
