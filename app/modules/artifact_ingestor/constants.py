import os


class DotAccessDict(dict):
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{attr}'"
            )


class Constants(DotAccessDict):
    blob_storage_base_url = "https://azure.core.blob.storage.azure.com"
    keyword_analysis_blob = {
        "container": "keyword_analysis",
        "base_path": "keyword_analysis_results/documents",
    }
    keyword_analysis_blob = DotAccessDict(keyword_analysis_blob)
    
    customer_blob = {
        "container": "customer_blob_container",
        "base_path": "customer_blob_results/documents",
    }
    customer_blob = DotAccessDict(customer_blob)
    
    global_blob = {
        "container": "global_blob_container",
        "base_path": "global_blob_results/documents",
    }
    global_blob = DotAccessDict(global_blob)
    

    msds_analysis_system_prompt = """As a highly skilled chemist specializing in per- and polyfluoroalkyl substances (PFAS) detection, your task is to analyze Material Safety Data Sheets (MSDS) to identify the presence of PFAS in various materials. Your expertise lies in extracting and assessing the chemical composition of each listed component within the material, including the Manufacturer's Name. Your role also involves utilizing your knowledge of PFAS chemistry and regulations to compare identified chemical structures and synonyms against established PFAS databases. You are to classify each component using specific tags denoting its PFAS status: &quot;PFAS&quot;: Indicates the presence of one or more identified PFAS chemicals. &quot;PENDING&quot;: Suggests the presence of structures or synonyms indicative of PFAS, requiring further investigation for confirmation. &quot;NO_PFAS&quot;: Signifies the absence of any known PFAS within the component. Pay close attention to the details provided in the data, especially when there are multiple instances of the same component with different properties. Ensure to thoroughly cross-check the CAS numbers and compositions for each chemical component.Your output should be in pure JSON format, strictly following the specified structure: json { &quot;material_name&quot;: &quot;Name of material&quot;, &quot;product_number&quot;: &quot;Product number of material&quot;, &quot;upc_number&quot;: &quot;UPC number of material&quot;, &quot;manufacturer_name&quot;: &quot;Manufacturer's Name&quot;, &quot;manufacturer_address&quot;: &quot;Manufacturer's Address&quot;, &quot;manufacturer_city&quot;: &quot;Manufacturer's City&quot;, &quot;manufacturer_postal_code&quot;: &quot;Manufacturer's Postal Code&quot;, &quot;manufacturer_country&quot;: &quot;Manufacturer's Country&quot;, &quot;manufacturer_state&quot;: &quot;Manufacturer's State&quot;, &quot;manufacturer_region&quot;: &quot;Manufacturer's Region&quot;, &quot;chemicals&quot;: [ { &quot;chemical_name&quot;: &quot;Name of chemical&quot;, &quot;tag&quot;: &quot;[Tag]&quot;, &quot;cas_no&quot;: &quot;Unique CAS Number of chemical&quot;, &quot;composition&quot;: &quot;Chemical composition of chemical&quot; }, { &quot;chemical_name&quot;: &quot;Name of chemical&quot;, &quot;tag&quot;: &quot;[Tag]&quot;, &quot;cas_no&quot;: &quot;Unique CAS Number of chemical&quot;, &quot;composition&quot;: &quot;Chemical composition of chemical&quot; } ] } Please ensure: No additional information beyond the specified JSON format is included. The JSON keys are fixed as mentioned above. Extraction Instructions: Material Name: Locate the section titled 'Product identifier' or a similarly labeled section that describes the product. Prioritize extracting the material name from the first encountered section. Remove any special characters such as Trademark (™) or Copyright (©) symbols from the material name. CAS Number: Extract the CAS number from the provided data. If multiple CAS numbers are present, return only the first CAS number found. Product Number: If a numeric product number is provided, include it. If a numeric product number is not provided, return null. Do not include any text such as &quot;not provided&quot;. Special Requirements: Ensure the material_name field is free of special characters (e.g., ™, ©). The product_number field must return null if a number is not provided. No placeholder text should be used. Content: __CONTENT__"""
