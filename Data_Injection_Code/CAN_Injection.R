#mydata = read.csv("data_embedded.csv",header = TRUE)  # read csv file 
#mydata

#head(mydata)
#trimmedData = mydata[c(1,4:11)]
#head(trimmedData)
#library(UsingR)
#library(corrplot)
#corrplot(trimmedData)
#plot(trimmedData)
#cor(trimmedData)
#corrplot(trimmedData, type="upper", order="hclust")
#write.csv(trimmedData,'trimmedData.csv')
library(csv)
#install.packages("ggvis")
#library(ggvis)

###############################
#Above is test/learning code
#The following code in the "inject" malicious code in
#to our data
#This malicious code edits the bytes and then changes
#data_type to a 0 for false, as in malicious
################################
trimmedDataModified = read.csv("trimmedData.csv",header = TRUE)
y = trimmedDataModified
#working with y 692800
for(q in 11:39){
y = trimmedDataModified
p = paste("trimmedMTestData_",q,".csv",sep="")  
#692878
for(i in 0:692878){
  x = runif(1)
if(x < 0.10){#edit this line for the ammount of data modified
  l = floor(runif(1, min=1, max=9))
  for(c in 1:l){
    n = floor(runif(1, min=2, max=10))
    v = y[i,n]

    y[i,n] = abs(v - runif(1,0,0.15))#edit this last number for the ammount a data value is changed
}
  y[i,10] = 0
}
  
}
q
write.csv(y,p, row.names=FALSE)
q
}
1+1







#############################
#The below code breakes up our gaint data set of over
#600k data points down to more usable data sets
#It breaks the code down to about 80% training and
#20% test data
############################
library(csv)
trimmedMData = read.csv("trimmedDataModified.csv",header = TRUE)
for(i in 0:69){
  if(i>0){
x = paste("trimmedMTestData_",i-1,".csv",sep="")  
}
  else{
    x = paste("trimmedMTrainingData.csv",sep="")  
      }
#print (x)
dataPoints = 10000
lower = i*dataPoints
upper = (i+1)*dataPoints
y = trimmedMData[lower:upper,]
write.csv(y,x, row.names=FALSE)
  }
1+1

