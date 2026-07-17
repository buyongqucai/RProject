source("配置.R", encoding = "UTF-8")
setup_script_env()


suppressPackageStartupMessages({
  library(GEOquery)
  library(tidyverse)
})

extract_affy_gene_symbols <- function(fdata, platform_id) {
  probe_ids <- rownames(fdata)

  db_map <- list(
    GPL6244 = "hugene10sttranscriptcluster.db"
  )

  if (platform_id %in% names(db_map)) {
    db_pkg <- db_map[[platform_id]]
    if (requireNamespace(db_pkg, quietly = TRUE)) {
      db <- get(db_pkg, envir = asNamespace(db_pkg))
      symbols <- AnnotationDbi::mapIds(
        db,
        keys = probe_ids,
        column = "SYMBOL",
        keytype = "PROBEID",
        multiVals = "first"
      )
      return(as.character(symbols))
    }
    message("Install ", db_pkg, " for better probe annotation.")
  }

  if ("gene_assignment" %in% colnames(fdata)) {
    return(vapply(fdata$gene_assignment, function(x) {
      if (is.na(x) || x == "---") return(NA_character_)
      block <- strsplit(x, " /// ", fixed = TRUE)[[1]][1]
      parts <- strsplit(block, " // ", fixed = TRUE)[[1]]
      if (length(parts) >= 2 && parts[2] != "---") parts[2] else NA_character_
    }, character(1)))
  }

  probe_ids
}

download_gse79962 <- function() {
  message("Downloading GSE79962 (human septic cardiomyopathy microarray)...")
  gse_list <- getGEO("GSE79962", destdir = PATHS$raw, GSEMatrix = TRUE, getGPL = TRUE)

  gse <- gse_list[[1]]
  expr <- Biobase::exprs(gse)
  pdata <- Biobase::pData(gse)
  fdata <- Biobase::fData(gse)

  # Prefer curated condition column; fall back to sample title
  if ("condition:ch1" %in% colnames(pdata)) {
    condition <- pdata[["condition:ch1"]]
  } else {
    condition <- pdata$title
  }

  group <- dplyr::case_when(
    grepl("septic cardiomyopathy", condition, ignore.case = TRUE) ~ "SCM",
    grepl("nonfailing heart", condition, ignore.case = TRUE) ~ "Control",
    TRUE ~ NA_character_
  )

  sample_label <- pdata$title

  keep <- !is.na(group)
  expr <- expr[, keep, drop = FALSE]
  group <- factor(group[keep], levels = c("Control", "SCM"))

  sample_info <- tibble(
    geo_accession = pdata$geo_accession[keep],
    title = sample_label[keep],
    group = group
  )
  rownames(sample_info) <- sample_info$geo_accession

  # Map probe IDs to gene symbols
  fdata$gene_symbol <- extract_affy_gene_symbols(fdata, annotation(gse))

  list(
    expr = expr,
    sample_info = sample_info,
    feature_info = fdata,
    platform = annotation(gse),
    data_type = "microarray"
  )
}

download_gse229925 <- function() {
  message("Downloading GSE229925 (mouse sepsis heart RNA-seq)...")
  gse_list <- getGEO("GSE229925", destdir = PATHS$raw, GSEMatrix = TRUE, getGPL = TRUE)

  gse <- gse_list[[1]]
  expr <- Biobase::exprs(gse)
  pdata <- Biobase::pData(gse)
  fdata <- Biobase::fData(gse)

  sample_label <- if ("title" %in% colnames(pdata) && any(nzchar(pdata$title))) {
    pdata$title
  } else {
    rownames(pdata)
  }

  group <- dplyr::case_when(
    grepl("\\bS\\b|sham", sample_label, ignore.case = TRUE) ~ "Sham",
    grepl("\\bC1\\b|HEF|high", sample_label, ignore.case = TRUE) ~ "HEF",
    grepl("\\bC2\\b|LEF|low", sample_label, ignore.case = TRUE) ~ "LEF",
    grepl("\\bC3\\b|NEF|normal", sample_label, ignore.case = TRUE) ~ "NEF",
    TRUE ~ NA_character_
  )

  if (any(is.na(group)) && "characteristics_ch1" %in% colnames(pdata)) {
    ch <- pdata$characteristics_ch1
    group[is.na(group) & grepl("sham", ch, ignore.case = TRUE)] <- "Sham"
    group[is.na(group) & grepl("HEF|high", ch, ignore.case = TRUE)] <- "HEF"
    group[is.na(group) & grepl("LEF|low", ch, ignore.case = TRUE)] <- "LEF"
    group[is.na(group) & grepl("NEF|normal", ch, ignore.case = TRUE)] <- "NEF"
  }

  if (any(is.na(group))) {
    warning("Some samples could not be assigned a group. Check sample labels.")
    print(tibble(label = sample_label, geo_accession = pdata$geo_accession)[is.na(group), ])
  }

  keep <- !is.na(group)
  expr <- expr[, keep, drop = FALSE]
  group <- factor(group[keep], levels = c("Sham", "HEF", "LEF", "NEF"))

  sample_info <- tibble(
    geo_accession = pdata$geo_accession[keep],
    title = sample_label[keep],
    group = group
  )
  rownames(sample_info) <- sample_info$geo_accession

  symbol_col <- intersect(c("Gene Symbol", "Symbol", "gene_assignment"), colnames(fdata))
  if (length(symbol_col) > 0 && symbol_col[1] == "gene_assignment") {
    fdata$gene_symbol <- extract_affy_gene_symbols(fdata, annotation(gse))
  } else if (length(symbol_col) > 0) {
    fdata$gene_symbol <- fdata[[symbol_col[1]]]
  } else {
    fdata$gene_symbol <- rownames(fdata)
  }

  list(
    expr = expr,
    sample_info = sample_info,
    feature_info = fdata,
    platform = annotation(gse),
    data_type = "rnaseq"
  )
}

download_dataset <- function(gse_id) {
  switch(gse_id,
    GSE79962 = download_gse79962(),
    GSE229925 = download_gse229925(),
    stop("Unsupported dataset: ", gse_id)
  )
}

data_obj <- download_dataset(DATASET)

prefix <- file.path(PATHS$中间数据, DATASET)
saveRDS(data_obj$expr, paste0(prefix, "_expr_raw.rds"))
saveRDS(data_obj$sample_info, paste0(prefix, "_sample_info.rds"))
saveRDS(data_obj$feature_info, paste0(prefix, "_feature_info.rds"))

write.csv(data_obj$sample_info, paste0(prefix, "_sample_info.csv"), row.names = FALSE)

message("Saved: ", nrow(data_obj$expr), " features x ", ncol(data_obj$expr), " samples")
message("Groups: ", paste(names(table(data_obj$sample_info$group)), table(data_obj$sample_info$group), sep = "=", collapse = ", "))
message("Done: 01_download_geo.R")