## Name: list_to_lipd
## Purpose: convert dataframe to lipd
## Author: Micheline Campbell
## Date created: 20200724
## Last edited: 20201130
## Edited by: MC
## Contact info: michelineleecampbell@gmail.com
## Notes:  This function based on code by Nick McKay (https://github.com/nickmckay/sisal2lipd).
  # input is a joined table, where columns are data and metadata and rows are observations. 


# packages ----------------------------------------------------------------

library(tidyverse)
library(lipdR)
library(here)


# function --------------------------------------------------------------------
list_lipd <- function(dat){
  
  
  database_name <- "PalaeoWISE" 

  
  pub <- vector(mode = "list", length = 1)
  pub[[1]]$journal <- dat$Journal[1]
  pub[[1]]$title <- dat$Title[1]
  pub[[1]]$citation <- dat$Citation[1]
  pub[[1]]$DOI <-dat$DOI[1]
  pub[[1]]$year <- dat$Year_pub[1]
  pub[[1]]$dataUrl <- dat$DataURL[1]
  pub[[1]]$authors <- dat$authors[1]
  pub[[1]]$author <- dat$AuthorLastName[1]
  pub[[1]]$otherRefs[[1]]$ref1 <- dat$OtherReferences1[1]
  pub[[1]]$otherRefs[[1]]$ref2 <- dat$OtherReferences2[1]
  pub[[1]]$otherRefs[[1]]$ref3 <- dat$OtherReferences3[1]
  pub[[1]]$otherRefs[[1]]$ref4 <- dat$OtherReferences4[1]
  pub[[1]]$dataCitation <- dat$Data_citation[1]
  
  ## GEO  - site metadata
  geo <- list()
  geo$siteName <- paste(dat$SourceLocName[1], dat$Region[1], sep = "_")
  geo$latitude <- dat$SourceLat1[1]
  geo$longitude <- dat$SourceLon1[1]
  geo$detailedCoordinates$source$values <- dat$sourcecoordinates[1]
  geo$detailedCoordinates$source$description <- "Bounding source coordinates (easternmost longitude, westernmost longitude, northernmost latitude, southernmost latitude, elevation)"
  geo$detailedCoordinates$target$values <- dat$targetcoordinates[1]
  geo$detailedCoordinates$target$description <- "Bounding reconstruction target coordinates (easternmost longitude, westernmost longitude, northernmost latitude, southernmost latitude, elevation)"
  
  
  
  ## Paleo - depth, age/year and proxy/reconstruction data
  ## general
  paleoData <- vector(mode = "list", length = 1)
  paleoData[[1]]$measurementTable[[1]]$tableName <- dat$DatasetName[1]
  paleoData[[1]]$measurementTable[[1]]$missingValue <- "NA"
  
  ## depth
  paleoData[[1]]$measurementTable[[1]]$depth$number <- 1
  paleoData[[1]]$measurementTable[[1]]$depth$variableName <- "depth"
  paleoData[[1]]$measurementTable[[1]]$depth$values <- dat$Depth
  paleoData[[1]]$measurementTable[[1]]$depth$description <- "depth below surface"
  paleoData[[1]]$measurementTable[[1]]$depth$units <- dat$Depth.Units[1]
  paleoData[[1]]$measurementTable[[1]]$depth$hasResolution$hasMaxValue <- max(dat$Depth)
  paleoData[[1]]$measurementTable[[1]]$depth$hasResolution$hasMeanValue <- mean(dat$Depth)
  paleoData[[1]]$measurementTable[[1]]$depth$hasResolution$hasMedianValue <- median(dat$Depth)
  paleoData[[1]]$measurementTable[[1]]$depth$hasResolution$hasMinValue <- min(dat$Depth)
  
  ##age
  paleoData[[1]]$measurementTable[[1]]$age$number <- 2
  paleoData[[1]]$measurementTable[[1]]$age$variableName <- "age"
  paleoData[[1]]$measurementTable[[1]]$age$units$units <- dat$AgeReference[1]
  paleoData[[1]]$measurementTable[[1]]$age$units$description <- "Reference point for reported ages"
  paleoData[[1]]$measurementTable[[1]]$age$units$confirmation$values <- dat$AgeRefConfirmation[1]
  paleoData[[1]]$measurementTable[[1]]$age$units$confirmation$description <- "Y = age reference was confirmed in either reference or communication with authors. "
  paleoData[[1]]$measurementTable[[1]]$age$description <- "Reported Age"
  
  paleoData[[1]]$measurementTable[[1]]$age$values <- dat$Age
  paleoData[[1]]$measurementTable[[1]]$age$uncertainty$uncertaintyPos <- dat$AgeUncertPos
  paleoData[[1]]$measurementTable[[1]]$age$uncertainty$uncertaintyNeg <- dat$AgeUncertNeg
  paleoData[[1]]$measurementTable[[1]]$age$hasResolution$hasMaxValue <- max(dat$Age)
  paleoData[[1]]$measurementTable[[1]]$age$hasResolution$hasMeanValue <- mean(dat$Age, na.rm = TRUE)
  paleoData[[1]]$measurementTable[[1]]$age$hasResolution$hasMedianValue <- median(dat$Age, na.rm = TRUE)
  paleoData[[1]]$measurementTable[[1]]$age$hasResolution$hasMinValue <- min(dat$Age)
  
  # year 
  paleoData[[1]]$measurementTable[[1]]$year$number <- 3
  paleoData[[1]]$measurementTable[[1]]$year$variableName <- 'Year CE/BCE'
  paleoData[[1]]$measurementTable[[1]]$year$values <- dat$Year
  paleoData[[1]]$measurementTable[[1]]$year$description <- "Year CE/BCE"
  paleoData[[1]]$measurementTable[[1]]$year$units <- "years"
  paleoData[[1]]$measurementTable[[1]]$year$hasResolution$hasMaxValue <- max(dat$Year)
  paleoData[[1]]$measurementTable[[1]]$year$hasResolution$hasMeanValue <- mean(dat$Year, na.rm = TRUE)
  paleoData[[1]]$measurementTable[[1]]$year$hasResolution$hasMedianValue <- median(dat$Year, na.rm = TRUE)
  paleoData[[1]]$measurementTable[[1]]$year$hasResolution$hasMinValue <- min(dat$Year)
  paleoData[[1]]$measurementTable[[1]]$year$startYear <- dat$StartYear[1]
  paleoData[[1]]$measurementTable[[1]]$year$endYear <- dat$EndYear[1]
  ## proxy
  proxy_name <- if_else(dat$DatasetType[1] == "Reconstruction",
                        paste(as.character(dat$ReconstructedParameter[1])),
                        paste(as.character(dat$ProxyType[1])))
  # proxy_name <- paste(as.character(dat$ProxyType[1]))
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$number <- 4
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$variableName <- proxy_name
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$coreName <- dat$CoreName[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$collectionName <- dat$CollectionName_NOAA[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$datasetType$type <- dat$DatasetType[1]
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$datasetType$description <- "Proxy or Reconstruction"
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$climateParameter <- dat$ClimateParameter[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$reconstructedParameter <- dat$ReconstructedParameter[1]
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$reconstructionMethod <- dat$ReconstructionMethod[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$interpretationFormat$format <- dat$InterpretationFormat[1]
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$interpretationFormat$description <- "Applicable to qualitative records - e.g. wet period = +2"
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$continuity <- dat$Continuity[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$resolution$qualitative <- dat$ResolutionQualitative[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$resolution$average <- dat$AverageResolution[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$overlap1ka$quantitative$value <- dat$OverlapWith1Ka[1]
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$overlap1ka$quantitative$description <- "Overlap with the last 1000 yrs (in years)"
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$overlap1ka$qualitative$value <- dat$Overlap_Qualitative[1]
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$overlap1ka$qualitative$description <- "High = >800 years overlap, Moderate = 400-800 years overlap, Low = <400 years of overlap with the last 1000 yrs (relative to 2019)."
  
  # paleoData[[1]]$measurementTable[[1]][[proxy_name]]$startYear <- dat$StartYear[1]
  # 
  # paleoData[[1]]$measurementTable[[1]][[proxy_name]]$endYear <- dat$EndYear[1]
  
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$units <- dat$Unit[1]
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$values <- dat$Value
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$variableType <- dat$DatasetType[1]
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$hasResolution$hasMaxValue <- max(dat$Value)
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$hasResolution$hasMeanValue <- mean(dat$Value, na.rm = TRUE)
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$hasResolution$hasMedianValue <- median(dat$Value, na.rm = TRUE)
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$hasResolution$hasMinValue <- min(dat$Value)
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$dataErrorPos <- dat$DataErrorPos
  paleoData[[1]]$measurementTable[[1]][[proxy_name]]$dataErrorNeg <- dat$DataErrorNeg
  
  paleoData[[1]]$measurementTable[[1]]$QC$number <- 5
  paleoData[[1]]$measurementTable[[1]]$QC$variableName <- "Quality Code"
  paleoData[[1]]$measurementTable[[1]]$QC$values <- dat$QC
  paleoData[[1]]$measurementTable[[1]]$QC$description <- "QC codes for data. 1 = raw, 4 = reconstruction, 21 = outlier, 22 = outlier ID needs to be revisted, 23 = outlier test not applied, 40 = NA"
  
  # combining all of the above into one list for write to lipd 
  L <- list()
  L$archiveType <- dat$ArchiveType[1]
  L$createdBy <- "SEQ_Palaeo_Team"
  L$dataSetName <- str_replace_all(dat$DatasetName[1], " ", "_")
  L$lipdName <- str_replace_all(paste0(dat$DatasetID[1],"_", dat$DatasetName[1], ".lpd"), " ", "_")
  L$lipdVersion <- 1.3
  L$referenceID <- dat$ReferenceID[1]
  L$dataSetID <- dat$DatasetID[1]
  L$siteID <- dat$SiteID[1]
  L$notes <- dat$Notes[1]
  L$funding <- dat$FundingDetails[1]
  L$geo <- geo
  L$pub <- pub
  L$paleoData <- paleoData
  
  L <<- L
  listname <<- str_replace_all(dat$DatasetName[1], " ", "_")
  
  filename <- paste0(L$dataSetID, "_", L$dataSetName, ".lpd")
  
  writeLipd(L,path = here(filename),ignore.warnings = TRUE)
}

# list_lipd(dat)
