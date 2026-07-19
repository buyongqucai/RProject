# Network preview: official STRING image (0.9 / 3D / no isolates) + R concentric fallback
# + herb–compound–target–pathway multilayer network
options(stringsAsFactors = FALSE)

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_all, value = TRUE)
script_path <- if (length(file_arg)) {
  normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
} else {
  normalizePath("02_run_network_preview.R", winslash = "/", mustWork = TRUE)
}
code_dir <- dirname(script_path)
sample_root <- normalizePath(file.path(code_dir, ".."), winslash = "/", mustWork = TRUE)
skill_root <- normalizePath(file.path(sample_root, ".."), winslash = "/", mustWork = TRUE)
bio_root <- normalizePath(file.path(skill_root, "..", ".."), winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(bio_root, "00_基础_Foundation"))) {
  bio_root <- normalizePath(file.path(skill_root, "..", "..", ".."), winslash = "/", mustWork = TRUE)
}

viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")
delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")

paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir <- paths$fig_dir
tab_dir <- paths$tab_dir
rep_dir <- paths$rep_dir
for (d in c(fig_dir, tab_dir, rep_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

scripts_dir <- file.path(skill_root, "脚本_scripts")
for (sf in list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)) {
  source(sf, encoding = "UTF-8")
}
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
required_score <- 900L  # STRING confidence 0.9

ov <- np_read_contract(data_dir, "overlap")
net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")
genes <- unique(as.character(ov$gene))
genes <- genes[!is.na(genes) & nzchar(genes)]
message("Overlap genes: ", length(genes), " · STRING required_score=", required_score)

ppi_cache <- file.path(data_dir, "PPI互作_StringInteractions_score900.tsv")
ppi_cache_out <- file.path(tab_dir, "19_PPI互作_StringInteractions_score900.tsv")

string_ok <- FALSE
image_ok <- FALSE
ppi <- NULL
string_err <- NULL
string_ids <- NULL

# 1) edges at score ≥ 0.9
tryCatch({
  ppi <- np_fetch_string_ppi(
    genes,
    species = 9606L,
    required_score = required_score,
    cache_path = ppi_cache,
    force = !file.exists(ppi_cache)
  )
  string_ids <- attr(ppi, "string_ids")
  file.copy(ppi_cache, ppi_cache_out, overwrite = TRUE)
  string_ok <- is.data.frame(ppi) && nrow(ppi) > 0
  message("STRING edges @0.9: ", nrow(ppi))
}, error = function(e) {
  string_err <<- conditionMessage(e)
  # fallback: filter legacy cache at 0.9
  legacy <- file.path(data_dir, "PPI互作_StringInteractions.tsv")
  if (file.exists(legacy)) {
    ppi <<- utils::read.delim(legacy, stringsAsFactors = FALSE, check.names = FALSE)
    string_ok <<- nrow(ppi) > 0
    message("Using legacy PPI cache filtered in plot (API failed: ", string_err, ")")
  }
})

# 2) Official STRING image: 3D structures, evidence edges, hide isolates
stem_official <- delivery_stem(skill_en, "network", "StringPPI", order = 13)
png_official <- file.path(fig_dir, paste0(stem_official, ".png"))
svg_official <- file.path(fig_dir, paste0(stem_official, ".svg"))

tryCatch({
  np_fetch_string_network_image(
    genes,
    out_path = png_official,
    species = 9606L,
    required_score = required_score,
    network_flavor = "evidence",
    hide_disconnected_nodes = TRUE,
    block_structure_pics = FALSE,
    show_query_node_labels = TRUE,
    format = "highres_image",
    string_ids = string_ids,
    timeout = 360
  )
  image_ok <- file.exists(png_official) && file.info(png_official)$size > 1000
  # also SVG if possible
  tryCatch({
    Sys.sleep(1)
    np_fetch_string_network_image(
      genes,
      out_path = svg_official,
      species = 9606L,
      required_score = required_score,
      network_flavor = "evidence",
      hide_disconnected_nodes = TRUE,
      block_structure_pics = FALSE,
      show_query_node_labels = TRUE,
      format = "svg",
      string_ids = string_ids,
      timeout = 360
    )
  }, error = function(e) message("STRING SVG skipped: ", conditionMessage(e)))
}, error = function(e) {
  string_err <<- paste(c(string_err, conditionMessage(e)), collapse = " | ")
  message("STRING official image failed: ", conditionMessage(e))
})

# 3) R PPI degree-gradient (concentric) — primary “PPI渐变图”
stem_deg <- delivery_stem(skill_en, "network", "StringPPI_Degree", order = 15)
if (isTRUE(string_ok)) {
  tryCatch({
    p_ppi <- np_plot_string_ppi(
      ppi,
      min_score = required_score,
      drop_isolates = TRUE,
      layout = "concentric",
      label_top_n = NULL
    )
    delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Degree", 11.5, 10.5, fig_dir, bio_root, order = 15)
    # also keep Concentric alias for older links
    delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Concentric", 11.5, 10.5, fig_dir, bio_root, order = 14)
    message("Saved PPI degree gradient: ", stem_deg)
  }, error = function(e) {
    message("R PPI degree plot failed: ", conditionMessage(e))
  })
} else {
  message("STRING PPI BLOCKED: ", string_err)
}

# 4) multilayer HCTP
cyto <- np_export_hctp_cytoscape(net, type_df, tab_dir)
message("Cytoscape tables: ", cyto$edges, " | ", cyto$nodes)
p_hctp <- np_plot_hctp_network(net, type_df)
delivery_save_plot(
  p_hctp, skill_en, "network", "HerbCompoundTargetPathway",
  14.5, 11.5, fig_dir, bio_root, order = 11
)
message("Saved HCTP delivery-layout network")

writeLines(
  c(
    paste0("STRING_PPI_official_image=", if (isTRUE(image_ok)) "PASS" else "BLOCKED_EXTERNAL"),
    paste0("STRING_PPI_degree_gradient=", if (file.exists(file.path(fig_dir, paste0(stem_deg, ".png")))) "PASS" else "FAIL"),
    paste0("HCTP_network_preview=PASS"),
    paste0("required_score=", required_score),
    paste0("string_edges=", if (!is.null(ppi)) nrow(ppi) else 0),
    paste0("string_error=", if (is.null(string_err)) "" else string_err),
    "layout=PPI concentric Degree; HCTP center-grid + herb satellites + flanking pathway hexes"
  ),
  file.path(rep_dir, "STATUS_network_preview.txt")
)
message("DONE — official=", image_ok, " edges=", string_ok)
