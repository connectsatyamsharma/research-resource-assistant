"""Builds the synthetic university knowledge-network dataset (data/university_kg.json).

All records are SYNTHETIC but modelled on a typical Indian university. They are written by hand for
this project (no copied data). Some records are deliberately incomplete (missing availability,
missing description) to exercise the exception-handling / human-review workflow.
"""
import json
from pathlib import Path

THEMES = [
    ("T01", "Medical Imaging", "radiology MRI CT scan X-ray tumor detection image segmentation diagnostic imaging lung scan"),
    ("T02", "Natural Language Processing", "text mining language models sentiment analysis chatbots machine translation transformers tweets Hindi"),
    ("T03", "Robotics", "autonomous robots drones manipulators motion planning SLAM navigation control warehouse automation"),
    ("T04", "Renewable Energy", "solar photovoltaic panels wind power battery storage smart grid energy"),
    ("T05", "Climate Modelling", "weather forecasting rainfall monsoon global warming carbon emissions remote sensing satellite"),
    ("T06", "Genomics", "DNA sequencing bioinformatics gene expression protein folding CRISPR biomarkers cancer genomics"),
    ("T07", "Cybersecurity", "intrusion detection malware network attacks security cryptography privacy"),
    ("T08", "Materials Science", "nanomaterials polymers alloys thin films coatings corrosion battery materials"),
    ("T09", "Smart Agriculture", "crop disease precision farming soil sensors irrigation yield prediction leaf photos"),
    ("T10", "Urban Mobility", "traffic congestion prediction IoT sensors smart city public transport vehicle routing logistics"),
]

# id, name, dept, availability(available|limited|unavailable|None), themes, description
LABS = [
    ("L01", "Medical Imaging and AI Lab", "CSE", "available", ["T01"],
     "Deep learning for radiology images: tumor segmentation in MRI and CT, chest X-ray screening, and explainable diagnostic models."),
    ("L02", "Language Intelligence Lab", "CSE", "available", ["T02"],
     "Builds language models and chatbots for Indian languages, sentiment analysis, code-mixed text and machine translation."),
    ("L03", "Autonomous Systems Lab", "Mechanical", "limited", ["T03", "T10"],
     "Mobile robots, drone navigation, SLAM and motion planning, with applications in warehouse logistics and vehicle routing."),
    ("L04", "Solar and Storage Research Lab", "Electrical", "available", ["T04", "T08"],
     "Photovoltaic performance monitoring, battery energy storage, degradation modelling and smart grid integration."),
    ("L05", "Climate Data Lab", "Civil", "available", ["T05", "T09"],
     "Rainfall and monsoon forecasting, satellite remote sensing and climate impact analysis for agriculture."),
    ("L06", "Computational Genomics Lab", "Biotechnology", "limited", ["T06", "T01"],
     "Gene expression analysis, DNA sequencing pipelines, cancer biomarker discovery and protein structure prediction."),
    ("L07", "Secure Systems Lab", "CSE", "available", ["T07"],
     "Network intrusion detection, malware analysis, applied cryptography and privacy-preserving machine learning."),
    ("L08", "Advanced Materials Lab", "Chemistry", "available", ["T08", "T04"],
     "Nanomaterials, anti-corrosion coatings, polymers and electrode materials for batteries."),
    ("L09", "Precision Agriculture Lab", "Agriculture", "available", ["T09", "T05"],
     "Crop disease detection from leaf images, soil sensors, irrigation scheduling and yield prediction."),
    ("L10", "Smart City and Mobility Lab", "Civil", "available", ["T10"],
     "Traffic congestion prediction, IoT sensor deployments, public transport analytics and urban planning."),
    ("L11", "Bio-Signal Processing Lab", "Electronics", "limited", ["T01"],
     "ECG and EEG signal analysis and wearable sensing, with growing work on medical image reconstruction."),
    ("L12", "Quantum Photonics Lab", "Physics", None, ["T08"], ""),  # INCOMPLETE: no availability, no description
]

DATASETS = [
    ("D01", "Chest X-ray Screening Subset", "CSE", "available", ["T01"], "L01",
     "12,000 de-identified chest X-ray images with radiologist labels for pneumonia and nodule screening."),
    ("D02", "Brain MRI Tumor Segmentation Set", "CSE", "limited", ["T01"], "L01",
     "480 annotated brain MRI volumes with tumor masks; access limited to approved student projects."),
    ("D03", "Indian-Language News Corpus", "CSE", "available", ["T02"], "L02",
     "1.2 million news articles in Hindi, Punjabi and English for language-model training and text classification."),
    ("D04", "Code-Mixed Hindi-English Tweets", "CSE", "available", ["T02"], "L02",
     "60,000 tweets labelled for sentiment and offensive language, useful for chatbots and sentiment analysis."),
    ("D05", "Warehouse Robot Trajectory Logs", "Mechanical", "available", ["T03", "T10"], "L03",
     "Sensor and trajectory logs from 8 mobile robots operating in a warehouse mock-up, including route plans."),
    ("D06", "Rooftop Solar Generation Logs", "Electrical", "available", ["T04"], "L04",
     "Two years of minute-level generation data from 40 rooftop photovoltaic panels on campus."),
    ("D07", "Battery Cycling Degradation Data", "Electrical", "limited", ["T04", "T08"], "L04",
     "Charge-discharge cycling records of lithium-ion cells for battery ageing and storage research."),
    ("D08", "District Rainfall 1990-2020", "Civil", "available", ["T05"], "L05",
     "Daily rainfall and temperature for Punjab districts, suitable for monsoon forecasting models."),
    ("D09", "Satellite Crop NDVI Time Series", "Agriculture", "available", ["T09", "T05"], "L09",
     "Satellite vegetation-index time series for wheat and paddy fields, linked to weather and yield records."),
    ("D10", "Plant Leaf Disease Images", "Agriculture", "available", ["T09"], "L09",
     "25,000 labelled leaf photographs of healthy and diseased crops for crop disease classification."),
    ("D11", "Cancer Gene Expression Cohort", "Biotechnology", "unavailable", ["T06"], "L06",
     "RNA gene expression profiles from a patient cohort; restricted pending ethics approval."),
    ("D12", "Network Intrusion Flow Records", "CSE", "available", ["T07"], "L07",
     "Labelled network traffic flows covering malware, port scans and denial-of-service attacks."),
    ("D13", "City Traffic Sensor Feed", "Civil", "available", ["T10"], "L10",
     "Six months of traffic counts and speeds from 120 road sensors for congestion prediction."),
    ("D14", "Alloy Corrosion Measurements", "Chemistry", "available", ["T08"], "L08",
     "Corrosion rate measurements for coated and uncoated alloys under salt-spray exposure."),
]

FACILITIES = [
    ("F01", "GPU Compute Cluster", "CSE", "limited", ["T01", "T02", "T06", "T09"], ["L01", "L02", "L06", "L09"],
     "Shared cluster of 16 GPUs for training large deep learning models; booked per week."),
    ("F02", "Sequencing Core Facility", "Biotechnology", "available", ["T06"], ["L06"],
     "Next-generation DNA sequencing service with bioinformatics support."),
    ("F03", "Robotics Arena", "Mechanical", "available", ["T03"], ["L03"],
     "Indoor arena with motion-capture for testing drones and mobile robot navigation."),
    ("F04", "Solar Test Field", "Electrical", "available", ["T04"], ["L04"],
     "Outdoor photovoltaic test field with calibrated irradiance and panel performance instrumentation."),
    ("F05", "Electron Microscopy Centre", "Chemistry", "limited", ["T08"], ["L08", "L12"],
     "Scanning electron microscope for nanomaterial, coating and thin-film characterisation."),
    ("F06", "Cyber Range", "CSE", "available", ["T07"], ["L07"],
     "Isolated virtual network for safe malware experiments and attack simulation."),
    ("F07", "Weather Station Network", "Civil", "available", ["T05", "T09"], ["L05", "L09"],
     "12 automatic weather stations across the campus farm and district for rainfall and climate records."),
    ("F08", "IoT Testbed", "Electronics", None, ["T10", "T07"], ["L10", "L07"],  # INCOMPLETE availability
     "Testbed of wireless sensor nodes for smart city and secure IoT experiments."),
]

# id, title, year, lab, themes, datasets
PUBS = [
    ("P01", "Explainable Tumor Segmentation in Brain MRI", 2024, "L01", ["T01"], ["D02"]),
    ("P02", "Chest X-ray Screening with Lightweight CNNs", 2023, "L01", ["T01"], ["D01"]),
    ("P03", "Sentiment Analysis on Code-Mixed Hindi-English Tweets", 2024, "L02", ["T02"], ["D04"]),
    ("P04", "Training Small Language Models for Punjabi News", 2025, "L02", ["T02"], ["D03"]),
    ("P05", "Reinforcement Learning for Warehouse Robot Routing", 2024, "L03", ["T03", "T10"], ["D05"]),
    ("P06", "Visual SLAM for Indoor Drone Navigation", 2023, "L03", ["T03"], []),
    ("P07", "Forecasting Rooftop Solar Output with LSTMs", 2024, "L04", ["T04"], ["D06"]),
    ("P08", "State-of-Health Estimation for Lithium-Ion Batteries", 2025, "L04", ["T04", "T08"], ["D07"]),
    ("P09", "Monsoon Rainfall Prediction for Punjab Districts", 2023, "L05", ["T05"], ["D08"]),
    ("P10", "Satellite-Based Wheat Yield Estimation", 2025, "L05", ["T05", "T09"], ["D09"]),
    ("P11", "Gene Expression Signatures for Cancer Subtyping", 2024, "L06", ["T06"], ["D11"]),
    ("P12", "Protein Structure Prediction on GPU Clusters", 2025, "L06", ["T06"], []),
    ("P13", "Anomaly-Based Network Intrusion Detection", 2024, "L07", ["T07"], ["D12"]),
    ("P14", "Privacy-Preserving Federated Learning for Malware Detection", 2025, "L07", ["T07"], ["D12"]),
    ("P15", "Graphene-Enhanced Anti-Corrosion Coatings", 2023, "L08", ["T08"], ["D14"]),
    ("P16", "Silicon Nanostructures for Battery Anodes", 2024, "L08", ["T08", "T04"], ["D07"]),
    ("P17", "Deep Learning for Crop Leaf Disease Classification", 2024, "L09", ["T09"], ["D10"]),
    ("P18", "Soil Moisture Sensing for Irrigation Scheduling", 2023, "L09", ["T09"], []),
    ("P19", "Graph Neural Networks for Urban Traffic Prediction", 2025, "L10", ["T10"], ["D13"]),
    ("P20", "Secure IoT Sensor Deployment for Smart Cities", 2024, "L10", ["T10", "T07"], ["D13"]),
    ("P21", "ECG-Assisted Medical Image Reconstruction", 2025, "L11", ["T01"], []),
]

def build():
    out = {
        "themes": [{"id": i, "type": "Theme", "name": n, "aliases": a} for i, n, a in THEMES],
        "labs": [{"id": i, "type": "Lab", "name": n, "dept": d, "availability": av, "themes": th, "description": ds}
                 for i, n, d, av, th, ds in LABS],
        "datasets": [{"id": i, "type": "Dataset", "name": n, "dept": d, "availability": av, "themes": th,
                      "owner_lab": ol, "description": ds} for i, n, d, av, th, ol, ds in DATASETS],
        "facilities": [{"id": i, "type": "Facility", "name": n, "dept": d, "availability": av, "themes": th,
                        "labs": lb, "description": ds} for i, n, d, av, th, lb, ds in FACILITIES],
        "publications": [{"id": i, "type": "Publication", "name": t, "year": y, "lab": lab, "themes": th,
                          "datasets": dsets} for i, t, y, lab, th, dsets in PUBS],
    }
    path = Path(__file__).resolve().parents[1] / "data" / "university_kg.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

if __name__ == "__main__":
    print("written", build())
