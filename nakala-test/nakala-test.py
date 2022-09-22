import os, sys
import requests
import yaml
import argparse
import time
import json

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--image")
args = parser.parse_args()

############################################################################################
# CREER UNE COLLECTION
############################################################################################
#
# url = 'https://apitest.nakala.fr/datas/uploads'
# verb = 'POST'
#
# headers = {
#     'X-API-KEY': "fc39c7c1-52de-e646-fc3f-ca88f6afe537",
#     'Content-Type': 'application/json'
# }
#
# content = {
#     "status": "public",
#     "metas" : [
#         {
#             "propertyUri": "http://nakala.fr/terms#title",
#             "value": "Estampes du Mercure Galant",
#             "typeUri": "http://www.w3.org/2001/XMLSchema#string",
#             "lang": "fr"
#         }
#     ]
# }
#
# createCollectionResponse = requests.request(verb, url, headers=headers, data=json.dumps(content))
# print(createCollectionResponse.status_code)
#
# parsedcreateCollectionResponse = json.loads(createCollectionResponse.text)
#
# print(json.dumps(parsedcreateCollectionResponse, indent=4))
#
# print(parsedcreateCollectionResponse["payload"]["id"])

# identifiant de collection test : 10.34847/nkl.692ab4nc


############################################################################################
# INSERER UNE IMAGE
############################################################################################
#
# url = 'https://apitest.nakala.fr/datas/uploads'
# verb = 'POST'
#
# headers = {
#     'X-API-KEY': "01234567-89ab-cdef-0123-456789abcdef"
# }
#
# content = {}
#
# files=[
#   ('file',('image-test.jpg',open(args.image,'rb')))
# ]
#
# responseUpload = requests.request(verb, url, headers=headers, data=content, files=files)
#
# # Affichons le contenu de la réponse de l'API
#
# if responseUpload.status_code == 201:
#     fileMetadata = responseUpload.text
#     print(fileMetadata)
# else:
#     print(responseUpload.text)
#
#
############################################################################################
# CREER UNE DONNEE
############################################################################################
#
# # On complète les informations récupérées précédemment lors de l'upload du fichier en ajoutant une date d'ouverture de fichier pour le rendre accessible à tous
#
# fileMetadataJson = json.loads(fileMetadata)
#
# # On affiche la liste des informations sur le fichier une fois les informations mises à jour
# print('Voici les informations associées au fichier : ')
# print(json.dumps(fileMetadataJson, indent=4))
#
# # On peut procéder ensuite à la création de la donnée à partir de ce fichier
#
# url = 'https://apitest.nakala.fr/datas'
# verb = 'POST'
#
# headers = {
#     'X-API-KEY': "01234567-89ab-cdef-0123-456789abcdef",
#     'Content-Type': 'application/json'
# }
#
# content = {
#     "status": "published",
#     "files" : [
#         # On ajoute ici les informations sur le fichier uploadé précédemment
#         fileMetadataJson
#     ],
#     # On ajoute ici quelques métadonnées pour décrire la donnée
#     "metas" : [
#         # le titre de la donnée
#         {
#             "propertyUri": "http://nakala.fr/terms#title",
#             "value": "Ma première image",
#             "typeUri": "http://www.w3.org/2001/XMLSchema#string",
#             "lang": "fr"
#         },
#         # le type de la donnée (image)
#         {
#             "propertyUri": "http://nakala.fr/terms#type",
#             "value": "http://purl.org/coar/resource_type/c_c513",
#             "typeUri": "http://www.w3.org/2001/XMLSchema#anyURI",
#         },
#         # le créateur de la donnée
#         {
#             "propertyUri": "http://nakala.fr/terms#creator",
#             "value": {
#                 "givenname": "Jean",
#                 "surname": "Dupont"
#             }
#         },
#         # la date de création de la donnée
#         {
#             "propertyUri": "http://nakala.fr/terms#created",
#             "value": "2020-01-01",
#             "typeUri": "http://www.w3.org/2001/XMLSchema#string"
#         },
#         # la licence associée à la donnée
#         {
#             "propertyUri": "http://nakala.fr/terms#license",
#             "value": "CC-BY-4.0",
#             "typeUri": "http://www.w3.org/2001/XMLSchema#string"
#         }
#     ]
# }
#
# createDataResponse = requests.request(verb, url, headers=headers, data=json.dumps(content))
#
# # On affiche la réponse de l'API
# print('Voici le code de réponse de l\'API suite à la demande de création de la donnée :')
# print(createDataResponse.status_code)
#
# print('Voici le contenu de la réponse :')
# print(createDataResponse.text)
#
# # Identifiant de la donnée : 10.34847\/nkl.de247m64


############################################################################################
# MODIFIER UNE COLLECTION
############################################################################################

url = 'https://apitest.nakala.fr/collections/10.34847/nkl.692ab4nc/datas'
verb = 'POST'

headers = {
    'X-API-KEY': "01234567-89ab-cdef-0123-456789abcdef",
    'Content-Type': 'application/json'
}

content = {["10.34847/nkl.de247m64"]}

modifyDataResponse = requests.request(verb, url, headers=headers, data=json.dumps(content))

# On affiche la réponse de l'API
print('Voici le code de réponse de l\'API suite à la demande de création de la donnée :')
print(modifyDataResponse.status_code)

print('Voici le contenu de la réponse :')
print(modifyDataResponse.text)


