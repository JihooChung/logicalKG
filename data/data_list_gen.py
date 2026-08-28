import pandas as pd

data = { "abstract_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
         "pmid": ["33508184", "35578724", "42017925", "36812168", "40012027", 
                    "34830745", "35909243", "33581689", "36457017", "35954379"],
         "title": ["Targeting Pancreatic Ductal Adenocarcinoma (PDAC).", 
                    "KIF22 Promotes Development of Pancreatic Cancer by Regulating the MEK/ERK/P21 Signaling Axis.", 
                    "Alpha-Fetoprotein Is a Potential Biomarker for Pancreatic Ductal Adenocarcinoma (PDAC): A Case Report.", 
                    "Transcriptomic analysis of pancreatic adenocarcinoma specimens obtained from Black and White patients.", 
                    "Pancreatic Ductal Adenocarcinoma (PDAC): Clinical Progress in the Last Five Years.", 
                    "Simple Serum Pancreatic Ductal Adenocarcinoma (PDAC) Protein Biomarkers:Is There Anything in Sight?", 
                    "Does acute pancreatitis herald pancreatic ductal adenocarcinoma? A multicenter electronic health research network study.", 
                    "Long non-coding RNA CERS6-AS1 facilitates the oncogenicity of pancreatic ductal adenocarcinoma by regulating the microRNA-15a-5p/FGFR1 axis.", 
                    "Multidrug resistance genes screening of pancreatic ductal adenocarcinoma based on sensitivity profile to chemotherapeutic drugs.", 
                    "Histone Deacetylase Inhibitors Restore Cancer Cell Sensitivity towards T Lymphocytes Mediated Cytotoxicity in Pancreatic Cancer."],
         "entities": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         "relations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

df = pd.DataFrame(data)
df.to_csv("./data/data_list.csv", index=False)
