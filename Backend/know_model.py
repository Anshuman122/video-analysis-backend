from google.generativeai import list_models

for model in list_models():
    print(model.name, model.supported_generation_methods)