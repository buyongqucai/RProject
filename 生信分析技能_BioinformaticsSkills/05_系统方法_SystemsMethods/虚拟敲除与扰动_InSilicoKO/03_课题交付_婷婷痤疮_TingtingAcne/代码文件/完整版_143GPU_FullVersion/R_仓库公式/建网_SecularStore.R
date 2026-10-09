# 建网公式来自同目录 pcNet_1.4.3.R，即 scTenifoldNet 1.4.3 的 pcNet。
# 本文件只加抽样记录、原子落盘和按网进度。不改 secular equation。
# 许可证与上游相同：GPL (>= 2)。原作者见该文件与包 DESCRIPTION。

pcnet_source <- function() {
  file_name <- utils::getSrcFilename(pcnet_source, full.names = TRUE)
  if (length(file_name) != 1 || !nzchar(file_name)) {
    stop("source 建网_SecularStore.R with keep.source = TRUE")
  }
  file.path(dirname(file_name), "pcNet_1.4.3.R")
}

load_pcnet <- function() {
  source(pcnet_source(), local = FALSE)
}

atomic_save <- function(object, path) {
  tmp <- paste0(path, ".partial")
  saveRDS(object, tmp)
  if (!file.rename(tmp, path)) {
    file.copy(tmp, path, overwrite = TRUE)
    unlink(tmp)
  }
}

draw_indices <- function(n_cells, n_draw, n_net, seed, out_dir) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  set.seed(seed)
  paths <- character(n_net)
  for (net_id in seq_len(n_net)) {
    path <- file.path(out_dir, sprintf("net_%02d_indices.rds", net_id))
    paths[[net_id]] <- path
    indices <- sample.int(n_cells, n_draw, replace = TRUE)
    if (file.exists(path) && file.info(path)$size > 0) {
      next
    }
    atomic_save(indices, path)
  }
  paths
}

parameters_match <- function(path, gene_names, n_comp, q) {
  if (!file.exists(path) || file.info(path)$size == 0) {
    return(FALSE)
  }
  stored <- tryCatch(readRDS(path), error = function(e) NULL)
  if (is.null(stored) || !is.list(stored)) {
    return(FALSE)
  }
  identical(stored$genes, gene_names) &&
    identical(as.integer(stored$n_comp), as.integer(n_comp)) &&
    identical(as.numeric(stored$q), as.numeric(q)) &&
    identical(stored$method, "secular143")
}

build_secular_networks <- function(counts, gene_names, out_dir,
                                   n_net = 10L, n_draw = 500L, n_comp = 3L,
                                   q = 0.9, seed = 1L,
                                   scale_scores = TRUE, symmetric = FALSE) {
  load_pcnet()
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  if (is.null(rownames(counts))) {
    rownames(counts) <- gene_names
  }
  index_paths <- draw_indices(ncol(counts), n_draw, n_net, seed, out_dir)
  done <- character(n_net)
  for (net_id in seq_len(n_net)) {
    net_path <- file.path(out_dir, sprintf("net_%02d.rds", net_id))
    mark_path <- file.path(out_dir, sprintf("net_%02d.done", net_id))
    if (file.exists(mark_path) && parameters_match(net_path, gene_names, n_comp, q)) {
      message(sprintf("网 %d/%d 跳过", net_id, n_net))
      done[[net_id]] <- net_path
      next
    }
    if (file.exists(mark_path)) unlink(mark_path)
    indices <- readRDS(index_paths[[net_id]])
    sub <- counts[, indices, drop = FALSE]
    keep <- rowSums(sub) > 0
    sub <- sub[keep, , drop = FALSE]
    message(sprintf("网 %d/%d 计算 基因 %d", net_id, n_net, nrow(sub)))
    network <- pcNet(sub, nComp = n_comp, scaleScores = scale_scores,
                     symmetric = symmetric, q = q, nCores = 1, verbose = FALSE)
    full <- matrix(0, nrow(counts), nrow(counts))
    rownames(full) <- colnames(full) <- gene_names
    full[rownames(network), colnames(network)] <- as.matrix(network)
    atomic_save(list(network = full, genes = gene_names, n_comp = as.integer(n_comp),
                     q = as.numeric(q), method = "secular143",
                     indices = as.integer(indices)), net_path)
    writeLines("ok", paste0(mark_path, ".partial"))
    file.rename(paste0(mark_path, ".partial"), mark_path)
    message(sprintf("网 %d/%d 已写入", net_id, n_net))
    done[[net_id]] <- net_path
  }
  done
}
