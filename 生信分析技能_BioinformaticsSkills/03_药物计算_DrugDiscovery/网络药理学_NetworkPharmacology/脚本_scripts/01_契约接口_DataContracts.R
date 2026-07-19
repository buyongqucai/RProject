# 网络药理学 — 数据契约（单药 × 分库；可替换 CSV）
# 对齐《网药数据解读》：禁止只用合并粗表掩盖单药/分库粒度。

#' 期望的输入文件契约（相对 data_dir）
np_data_contracts <- function() {
  list(
    herb_targets_pattern = list(
      file = "药物_*_靶点基因_HerbTargets.csv",
      required_cols = c("herb_zh", "herb_en", "gene"),
      source_hint = "Per-herb TCMSP→UniProt export"
    ),
    herb_overlap_pattern = list(
      file = "药物_*_疾病交集_HerbDiseaseOverlap.csv",
      required_cols = c("herb_zh", "herb_en", "gene"),
      source_hint = "Per-herb targets ∩ disease union"
    ),
    drug_union = list(
      file = "药物去重基因_DrugGenesUnion.csv",
      required_cols = c("gene"),
      source_hint = "union of all herb target genes"
    ),
    disease_by_db = list(
      file = "疾病靶点按库_DiseaseGenesByDB.csv",
      required_cols = c("gene", "source"),
      source_hint = "GeneCards(filtered)/TTD/DrugBank/OMIM — downstream"
    ),
    disease_by_db_venn = list(
      file = "疾病靶点按库_VennFull_DiseaseGenesByDB.csv",
      required_cols = c("gene", "source"),
      source_hint = "FULL GeneCards + TTD/DrugBank/OMIM — disease multi-DB Venn only"
    ),
    disease_union = list(
      file = "疾病靶点合并_DiseaseGenesUnion.csv",
      required_cols = c("gene"),
      source_hint = "union of multi-DB disease genes"
    ),
    overlap = list(
      file = "药物疾病交集_DrugDiseaseOverlap.csv",
      required_cols = c("gene"),
      source_hint = "drug_union ∩ disease_union"
    ),
    per_herb_summary = list(
      file = "单药疾病交集汇总_PerHerbOverlapSummary.csv",
      required_cols = c("herb_zh", "herb_en", "n_overlap_genes"),
      source_hint = "derived per-herb overlap counts"
    ),
    network = list(
      file = "网络边_network.csv",
      required_cols = NULL,
      source_hint = "Cytoscape input edges (herb–compound, compound–target)"
    ),
    type_table = list(
      file = "网络节点类型_type.csv",
      required_cols = NULL,
      source_hint = "A=herb B=compound C=target D=KEGG pathway"
    ),
    ppi = list(
      file = "PPI互作_StringInteractions.tsv",
      required_cols = NULL,
      source_hint = "STRING API or web export (preferredName_A/B or node1/node2)"
    ),
    go_bubble = list(
      file = "富集GO_BPCCMF_Bubble.csv",
      required_cols = c("term", "enrichment", "pvalue", "count", "ontology"),
      source_hint = "Metascape / clusterProfiler GO"
    ),
    kegg = list(
      file = "富集KEGG_TopPathways.csv",
      required_cols = NULL,
      source_hint = "KEGG enrichment table"
    ),
    compound_targets = list(
      file = "药物成分靶点_CompoundTargets.csv",
      required_cols = c("herb", "compound_id", "target_gene"),
      source_hint = "Per-herb compound→gene edges with Mol Rename IDs"
    ),
    compound_rename = list(
      file = "成分重命名_CompoundRenameMap.csv",
      required_cols = c("compound_name", "compound_id", "herb_code"),
      source_hint = "Delivery 重复有效成分命名表 → Mol Rename"
    ),
    herb_compound_edges = list(
      file = "草药成分边_HerbCompoundEdges.csv",
      required_cols = c("herb_code", "compound_id", "herb"),
      source_hint = "Herb code → Mol Rename membership"
    ),
    # derived / legacy optional
    derived_edges = list(
      file = "派生_成分靶点边_DerivedCompoundTargets.csv",
      required_cols = c("herb", "compound_id", "target_gene"),
      source_hint = "DERIVED from TCMSP per-herb tables; not a substitute for per-herb files"
    )
  )
}

#' 读取并校验契约表
np_read_contract <- function(data_dir, key, required = TRUE) {
  contracts <- np_data_contracts()
  if (!key %in% names(contracts)) stop("未知契约 key: ", key, call. = FALSE)
  spec <- contracts[[key]]
  path <- file.path(data_dir, spec$file)
  if (!file.exists(path)) {
    if (!required) return(NULL)
    stop("缺少契约文件: ", path, " — ", spec$source_hint, call. = FALSE)
  }
  sep <- if (grepl("\\.tsv$", path, ignore.case = TRUE)) "\t" else ","
  df <- utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE,
                        fileEncoding = "UTF-8", sep = sep)
  if (!is.null(spec$required_cols)) {
    miss <- setdiff(spec$required_cols, names(df))
    if (length(miss)) {
      stop(spec$file, " 缺列: ", paste(miss, collapse = ", "), call. = FALSE)
    }
  }
  df
}

#' 列出单药靶点文件
np_list_herb_target_files <- function(data_dir) {
  list.files(data_dir, pattern = "^药物_.+_靶点基因_HerbTargets\\.csv$", full.names = TRUE)
}

#' 列出单药疾病交集文件
np_list_herb_overlap_files <- function(data_dir) {
  list.files(data_dir, pattern = "^药物_.+_疾病交集_HerbDiseaseOverlap\\.csv$", full.names = TRUE)
}

#' 读取全部单药靶点
np_read_all_herb_targets <- function(data_dir) {
  files <- np_list_herb_target_files(data_dir)
  if (!length(files)) stop("未找到单药靶点文件 药物_*_靶点基因_HerbTargets.csv", call. = FALSE)
  dfs <- lapply(files, function(f) {
    utils::read.csv(f, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
  })
  do.call(rbind, dfs)
}

#' 读取全部单药疾病交集
np_read_all_herb_overlaps <- function(data_dir) {
  files <- np_list_herb_overlap_files(data_dir)
  if (!length(files)) stop("未找到单药交集文件", call. = FALSE)
  dfs <- lapply(files, function(f) {
    utils::read.csv(f, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
  })
  do.call(rbind, dfs)
}

#' 全药靶点 ∩ 疾病靶点
np_compute_overlap <- function(drug_genes, disease_genes) {
  ct <- unique(as.character(drug_genes$gene))
  dg <- unique(as.character(disease_genes$gene))
  hit <- sort(intersect(ct, dg))
  data.frame(gene = hit, stringsAsFactors = FALSE)
}

#' 分库基因列表（named list）供韦恩图
np_disease_sets <- function(disease_by_db) {
  srcs <- sort(unique(as.character(disease_by_db$source)))
  out <- lapply(srcs, function(s) {
    unique(as.character(disease_by_db$gene[disease_by_db$source == s]))
  })
  names(out) <- srcs
  out
}

#' 草药英文名 / 草药码对照
np_herb_code_map <- function() {
  data.frame(
    herb_code = c("DS", "HL", "RS", "HQ", "GG", "SQ"),
    herb_en = c("Danshen", "Huanglian", "Renshen", "Huangqi", "Gegen", "Sanqi"),
    herb_zh = c("丹参", "黄连", "人参", "黄芪", "葛根", "三七"),
    stringsAsFactors = FALSE
  )
}

#' 成分–靶点边 × 药病交集基因 → 成分–交集靶点边表
#'
#' @param ct data.frame with herb, compound_id, target_gene
#'   (optional: compound_name, herb_code, herb_zh, herb_en)
#' @param overlap_genes character vector or data.frame with column gene
#' @param rename_map optional data.frame compound_name, compound_id, herb_code
#' @param herb_compound_edges optional herb_code, compound_id, herb
np_build_compound_disease_overlap_edges <- function(ct,
                                                    overlap_genes,
                                                    rename_map = NULL,
                                                    herb_compound_edges = NULL) {
  if (is.null(ct) || !nrow(ct)) {
    stop("compound_targets is empty", call. = FALSE)
  }
  need <- c("herb", "compound_id", "target_gene")
  miss <- setdiff(need, names(ct))
  if (length(miss)) stop("ct 缺列: ", paste(miss, collapse = ", "), call. = FALSE)

  ov <- if (is.data.frame(overlap_genes)) {
    unique(as.character(overlap_genes$gene))
  } else {
    unique(as.character(overlap_genes))
  }
  ov <- ov[!is.na(ov) & nzchar(ov)]
  if (!length(ov)) stop("overlap_genes is empty", call. = FALSE)

  df <- ct
  df$herb <- as.character(df$herb)
  df$compound_id <- as.character(df$compound_id)
  df$target_gene <- as.character(df$target_gene)
  df <- df[!is.na(df$target_gene) & nzchar(df$target_gene), , drop = FALSE]
  df$in_disease_overlap <- df$target_gene %in% ov
  df <- df[df$in_disease_overlap, , drop = FALSE]
  if (!nrow(df)) {
    warning("No compound–target edges intersect disease-overlap genes")
    return(df[0, , drop = FALSE])
  }

  hmap <- np_herb_code_map()
  # herb_en from ct$herb (sample uses English herb names)
  if (!"herb_en" %in% names(df)) df$herb_en <- df$herb
  if (!"herb_zh" %in% names(df)) {
    df$herb_zh <- hmap$herb_zh[match(df$herb_en, hmap$herb_en)]
    df$herb_zh[is.na(df$herb_zh)] <- df$herb_en[is.na(df$herb_zh)]
  }
  if (!"herb_code" %in% names(df) || all(is.na(df$herb_code) | !nzchar(as.character(df$herb_code)))) {
    if (!is.null(herb_compound_edges) && nrow(herb_compound_edges)) {
      hc <- unique(herb_compound_edges[, c("compound_id", "herb_code", "herb"), drop = FALSE])
      df$herb_code <- hc$herb_code[match(df$compound_id, hc$compound_id)]
      # shared same* may map to multiple herbs — prefer herb column match
      for (i in which(is.na(df$herb_code) | !nzchar(df$herb_code))) {
        hit <- hc$herb_code[hc$compound_id == df$compound_id[i] &
                              tolower(hc$herb) == tolower(df$herb_en[i])]
        if (length(hit)) df$herb_code[i] <- hit[1]
      }
    }
    still <- is.na(df$herb_code) | !nzchar(as.character(df$herb_code))
    df$herb_code[still] <- hmap$herb_code[match(df$herb_en[still], hmap$herb_en)]
  }

  if (!"compound_name" %in% names(df) || all(is.na(df$compound_name) | !nzchar(as.character(df$compound_name)))) {
    if (!is.null(rename_map) && nrow(rename_map)) {
      rm <- rename_map
      # join by compound_id (+ herb_code when available)
      key_rm <- paste(rm$compound_id, rm$herb_code, sep = "||")
      key_df <- paste(df$compound_id, df$herb_code, sep = "||")
      df$compound_name <- rm$compound_name[match(key_df, key_rm)]
      miss_nm <- is.na(df$compound_name) | !nzchar(df$compound_name)
      df$compound_name[miss_nm] <- rm$compound_name[match(df$compound_id[miss_nm], rm$compound_id)]
    } else {
      df$compound_name <- df$compound_id
    }
  }

  df$compound_id_mapped <- !(is.na(df$compound_id) | !nzchar(df$compound_id) |
                               grepl("^UNMAPPED", df$compound_id, ignore.case = TRUE))

  out <- data.frame(
    herb_zh = as.character(df$herb_zh),
    herb_en = as.character(df$herb_en),
    herb_code = as.character(df$herb_code),
    compound_name = as.character(df$compound_name),
    compound_id = as.character(df$compound_id),
    target_gene = as.character(df$target_gene),
    in_disease_overlap = TRUE,
    compound_id_mapped = as.logical(df$compound_id_mapped),
    stringsAsFactors = FALSE
  )
  out <- unique(out)
  rownames(out) <- NULL
  out
}

#' 按成分汇总交集靶点数
np_summarize_compound_overlap <- function(edges) {
  if (is.null(edges) || !nrow(edges)) {
    return(data.frame(
      compound_id = character(),
      compound_name = character(),
      n_overlap_targets = integer(),
      n_herbs = integer(),
      herbs = character(),
      stringsAsFactors = FALSE
    ))
  }
  split_ids <- split(edges, edges$compound_id)
  rows <- lapply(names(split_ids), function(cid) {
    d <- split_ids[[cid]]
    nm <- d$compound_name[1]
    if (is.na(nm) || !nzchar(nm)) nm <- cid
    herbs <- sort(unique(d$herb_en))
    data.frame(
      compound_id = cid,
      compound_name = nm,
      n_overlap_targets = length(unique(d$target_gene)),
      n_herbs = length(herbs),
      herbs = paste(herbs, collapse = ";"),
      stringsAsFactors = FALSE
    )
  })
  out <- do.call(rbind, rows)
  out <- out[order(-out$n_overlap_targets, out$compound_id), , drop = FALSE]
  rownames(out) <- NULL
  out
}

#' 导出 Cytoscape 风格边/节点（药–成分、成分–交集基因）
np_export_compound_gene_cytoscape <- function(edges, herb_compound_edges = NULL) {
  if (is.null(edges) || !nrow(edges)) {
    return(list(
      network = data.frame(ID = character(), SYMBOL = character(), stringsAsFactors = FALSE),
      type = data.frame(term = character(), type = character(), stringsAsFactors = FALSE)
    ))
  }
  # herb → compound
  if (!is.null(herb_compound_edges) && nrow(herb_compound_edges)) {
    hc <- unique(herb_compound_edges[, c("herb_code", "compound_id"), drop = FALSE])
    # keep only compounds present in overlap edges
    hc <- hc[hc$compound_id %in% unique(edges$compound_id), , drop = FALSE]
    e1 <- data.frame(ID = hc$herb_code, SYMBOL = hc$compound_id, stringsAsFactors = FALSE)
  } else {
    e1 <- unique(data.frame(
      ID = edges$herb_code,
      SYMBOL = edges$compound_id,
      stringsAsFactors = FALSE
    ))
    e1 <- e1[!is.na(e1$ID) & nzchar(e1$ID) & !is.na(e1$SYMBOL) & nzchar(e1$SYMBOL), , drop = FALSE]
  }
  # compound → gene
  e2 <- unique(data.frame(
    ID = edges$compound_id,
    SYMBOL = edges$target_gene,
    stringsAsFactors = FALSE
  ))
  e2 <- e2[!is.na(e2$ID) & nzchar(e2$ID) & !is.na(e2$SYMBOL) & nzchar(e2$SYMBOL), , drop = FALSE]
  # drop unmapped compound ids from cytoscape export
  keep <- !grepl("^UNMAPPED", e2$ID, ignore.case = TRUE)
  e2 <- e2[keep, , drop = FALSE]
  e1 <- e1[e1$SYMBOL %in% e2$ID, , drop = FALSE]

  net <- rbind(e1, e2)
  herbs <- unique(e1$ID)
  comps <- unique(e1$SYMBOL)
  genes <- unique(e2$SYMBOL)
  typ <- rbind(
    data.frame(term = herbs, type = "A", stringsAsFactors = FALSE),
    data.frame(term = comps, type = "B", stringsAsFactors = FALSE),
    data.frame(term = genes, type = "C", stringsAsFactors = FALSE)
  )
  typ <- unique(typ)
  list(network = net, type = typ)
}
