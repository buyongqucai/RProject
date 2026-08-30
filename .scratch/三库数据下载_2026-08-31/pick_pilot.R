library(readxl)
d <- as.data.frame(read_excel("D:/数据库/KEGG数据库/KEGG通路动画映射表.xlsx"))
todo <- d[d[["动画状态"]] == "待绘制" & d[["排名"]] <= 183, ]
man <- read.csv("E:/RProject/努力学习项目/网络药理学/交付文件/图片/KEGG官方通路图/00_全部通路图清单.csv",
                fileEncoding = "UTF-8-BOM")
m <- todo[todo[["排名"]] %in% man$rank, ]
cat("todo:", nrow(todo), " in-manifest:", nrow(m), "\n")
print(m[, c("排名", "KEGG编号", "通路中文名", "通路英文名")])
