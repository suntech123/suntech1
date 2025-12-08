#!/bin/bash

# --- CONFIGURATION ---
# REPLACE these paths with the actual locations of your source folders
FOLDER_A="/Users/yourname/path/to/folder_a"
FOLDER_B="/Users/yourname/path/to/folder_b"
# The destination is the current folder where you run this script
DESTINATION="."

# List of files extracted from your image
files=(
    "COC26-INS-2018-SG-AL-349c561c-2592-4970-9099-01faecaea2e2.tsv"
    "COC26-INS-2018-SG-AK-ea9076a8-a627-4764-9d85-fa4a25ef5074.tsv"
    "COC26-INS-2018-SG-AR-462b58d2-e8ef-4ec3-994c-31642d4d6176.tsv"
    "COC26-INS-2018-SG-CO-0138edf9-581f-4840-b138-02d104f0f3ec.tsv"
    "COC26-INS-2018-SG-DE-08c1f45d-721b-47c1-9040-3d6550b0c012.tsv"
    "COC26-INS-2018-SG-FL-93c1e89e-3234-4b41-aa20-64f1e38c09c3.tsv"
    "COC26-INS-2018-SG-GA-e6d86c4d-035b-44b7-99eb-1641d15d64b0.tsv"
    "COC26-INS-2018-SG-HI-d7ec9308-0802-4bff-8498-f206cbbbcabc.tsv"
    "COC26-INS-2018-SG-IA-186f7fa1-bfde-4064-b967-0f523d83729f.tsv"
    "COC26-INS-2018-SG-ID-d7dfe654-eff5-4db0-aa7d-cfd9bb0e2e9e.tsv"
    "COC26-INS-2018-SG-IL-bbe021ad-cab8-4fba-91f5-2978d7e07f59.tsv"
    "COC26-INS-2018-SG-IN-WITH OBESITY-4a9af6e5-95f3-4d85-a5fd-4a9ce207b92b.tsv"
    "COC26-INS-2018-SG-KY-8f591af4-2c5f-4813-83fc-efe8994e9823.tsv"
    "COC26-INS-2018-SG-LA-REV1-318aaff7-00bb-4faa-a651-ad61ee9511f5.tsv"
    "COC26-INS-2018-SG-MA-96eb285a-277d-449c-a644-8504246d6dd3.tsv"
    "COC26-INS-2018-SG-MD-21078163-a32d-4fc3-a66b-9299f2057fe4.tsv"
    "COC26-INS-2018-SG-ME-REV1-912b31ec-fd2f-4f4f-af8a-ba86f823eeb5.tsv"
    "COC26-INS-2018-SG-MI-CHP-EMBEDDED-debcd755-1b9f-49ad-8a5a-8b5318ca3a28.tsv"
    "COC26-INS-2018-SG-MN-7230b651-d1e0-42cd-aeaf-78f478015af4.tsv"
    "COC26-INS-2018-SG-MO-75fe7493-0c45-4c95-b02c-17352fc0652b.tsv"
    "COC26-INS-2018-SG-MT-bcd8d27b-fbf8-4b27-bb33-1588a13bd9c1.tsv"
    "COC26-INS-2018-SG-NC-0e1349d7-20a8-4ae9-9d95-7881b2f19821.tsv"
    "COC26-INS-2018-SG-ND-7ee9b89e-99f2-42a6-b7a9-17e8c7a76e24.tsv"
    "COC26-INS-2018-SG-NE-e291e25a-b506-44f1-b0d4-9881699272a2.tsv"
    "COC26-INS-2018-SG-NH-b3cf5ae5-0d4b-44ad-a747-53fdc96566fe.tsv"
    "COC26-INS-2018-SG-NM-R1-75ffd33e-69f6-4f62-aac6-457c4103562b.tsv"
    "COC26-INS-2018-SG-OH-8fb28280-4579-4f34-85bb-783cb913a4ec.tsv"
    "COC26-INS-2018-SG-OK-790e59f8-0a93-42cf-ae2e-1bf4f13c02c5.tsv"
    "COC26-INS-2018-SG-OR-UHIC-NET-00N-ORSTD-77abd2d5-f353-42da-9ad2-64f1734b3412.tsv"
    "COC26-INS-2018-SG-PA-a9486d82-660d-425a-a75d-9b3197485e75.tsv"
    "COC26-INS-2018-SG-PPO-KS-0da20006-164f-4182-a662-17ee34e40ddf.tsv"
    "COC26-INS-2018-SG-SC-3ef8dbf2-6a5c-409f-9b30-b085855194d2.tsv"
    "COC26-INS-2018-SG-SD-62ff7677-ae55-45af-8fc8-7374c76b2f01.tsv"
    "COC26-INS-2018-SG-TN-fdf10f3e-7b04-4dab-9a57-d648363c91dc.tsv"
    "COC26-INS-2018-SG-TX-f72e59d4-5adf-4106-b386-e308242b08bc.tsv"
    "COC26-INS-2018-SG-UHIC-WA-NEXUS-3fff4393-be27-4f06-8bc6-3576c552115d.tsv"
    "COC26-INS-2018-SG-UT-3f68191c-4fd0-443c-be82-ded11fedcf04.tsv"
    "COC26-INS-2018-SG-VA-367a6d58-d85e-4ac2-bc55-1d350f68f9dd.tsv"
    "COC26-INS-2018-SG-VI-d50f3a2b-3fd1-4be1-bf09-402c10e8df23.tsv"
    "COC26-INS-2018-SG-WV-780b7e61-f6e3-4ec1-965d-6be9f2b8224a.tsv"
    "COC26-INS-2018-SG-WY-cb6c23b8-3431-45f0-8b6e-a10cf57d1afb.tsv"
    "COC26-INS-2018-SHOP-SG-DC-3c60e730-baf5-487b-8870-2ca038fd66b4.tsv"
)

# --- EXECUTION ---
echo "Starting file move operation..."
echo "Checking Folder A: $FOLDER_A"
echo "Checking Folder B: $FOLDER_B"
echo "--------------------------------"

for file in "${files[@]}"; do
    # Check if file exists in Folder A
    if [ -f "$FOLDER_A/$file" ]; then
        echo "✅ Found in Folder A: $file"
        mv "$FOLDER_A/$file" "$DESTINATION"
        
    # Check if file exists in Folder B
    elif [ -f "$FOLDER_B/$file" ]; then
        echo "✅ Found in Folder B: $file"
        mv "$FOLDER_B/$file" "$DESTINATION"
        
    # File found in neither
    else
        echo "❌ MISSING: Could not find $file in either location."
    fi
done

echo "--------------------------------"
echo "Operation complete."