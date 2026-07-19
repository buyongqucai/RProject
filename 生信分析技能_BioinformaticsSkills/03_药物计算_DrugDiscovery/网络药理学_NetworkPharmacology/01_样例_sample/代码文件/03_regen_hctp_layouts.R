# Regenerate columns + ellipse HCTP and STRING PPI degree/concentric delivery networks
options(stringsAsFactors = FALSE)

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_all, value = TRUE)
script_path <- if (length(file_arg)) {
  normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
} else {
  normalizePath("03_regen_hctp_layouts.R", winslash = "/", mustWork = TRUE)
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
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

scripts_dir <- file.path(skill_root, "脚本_scripts")
script_files <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
# Delivery layouts must win over 03_* plot helpers
delivery_sf <- grep("04_交付网络布局", script_files, value = TRUE)
other_sf <- setdiff(script_files, delivery_sf)
for (sf in c(other_sf, delivery_sf)) {
  source(sf, encoding = "UTF-8")
}
if (exists("setup_cjk_fonts")) setup_cjk_fonts()

skill_en <- "NetworkPharmacology"
net <- np_read_contract(data_dir, "network")
type_df <- np_read_contract(data_dir, "type_table")
message("Loaded network rows=", nrow(net), " type rows=", nrow(type_df))

# --- A) columns HCTP (taller canvas for vertical pitch + type-constant fonts) ---
p_col <- np_plot_hctp_network(net, type_df, pathway_mode = "columns")
delivery_save_plot(
  p_col, skill_en, "network", "HerbCompoundTargetPathway",
  18.5, 16.5, fig_dir, bio_root, order = 11
)
message("Saved columns HCTP")

# --- B) ellipse HCTP ---
p_ell <- np_plot_hctp_network(net, type_df, pathway_mode = "ellipse")
delivery_save_plot(
  p_ell, skill_en, "network", "HerbCompoundTargetPathway_Ellipse",
  18.5, 16.5, fig_dir, bio_root, order = 12
)
message("Saved ellipse HCTP")

# --- C) STRING PPI Degree + Concentric alias ---
ppi <- NULL
result_data <- paths$tab_dir
ppi_candidates <- c(
  file.path(data_dir, "PPI互作_StringInteractions_score900.tsv"),
  file.path(result_data, "19_PPI互作_StringInteractions_score900.tsv"),
  file.path(result_data, "PPI互作_StringInteractions_score900.tsv"),
  file.path(data_dir, "PPI互作_StringInteractions.tsv"),
  file.path(result_data, "20_PPI互作_StringInteractions.tsv"),
  file.path(result_data, "PPI互作_StringInteractions.tsv")
)
ppi_candidates <- c(
  ppi_candidates,
  list.files(data_dir, pattern = "StringInteractions|STRING|ppi", full.names = TRUE, ignore.case = TRUE),
  list.files(result_data, pattern = "StringInteractions|STRING|ppi", full.names = TRUE, ignore.case = TRUE)
)
ppi_candidates <- unique(ppi_candidates[file.exists(ppi_candidates)])
# prefer score900 filtered table
pref <- grep("score900", ppi_candidates, value = TRUE)
if (length(pref)) ppi_candidates <- c(pref, setdiff(ppi_candidates, pref))
if (length(ppi_candidates)) {
  ppi_path <- ppi_candidates[[1]]
  message("Loading PPI: ", ppi_path)
  ppi <- tryCatch(
    utils::read.delim(ppi_path, stringsAsFactors = FALSE, check.names = FALSE),
    error = function(e) {
      message("PPI read failed: ", conditionMessage(e))
      NULL
    }
  )
} else {
  message("No local PPI TSV found")
}

if (!is.null(ppi) && nrow(ppi) > 0) {
  p_ppi <- np_plot_string_ppi(
    ppi,
    min_score = 900L,
    drop_isolates = TRUE,
    layout = "concentric",
    label_top_n = NULL,
    outer_frac = 0.50
  )
  delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Degree", 11.5, 10.5, fig_dir, bio_root, order = 15)
  delivery_save_plot(p_ppi, skill_en, "network", "StringPPI_Concentric", 11.5, 10.5, fig_dir, bio_root, order = 14)
  message("Saved PPI Degree + Concentric")
} else {
  message("SKIP PPI regen — no PPI table available")
}

message("DONE")
