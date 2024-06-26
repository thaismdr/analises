# -*- coding: utf-8 -*-
"""slaves.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WUYbSWr24YGnq_xQaY9Wc5gpAnvSIDVQ
"""

#Análise da BD Letter de Abril/2023
#1ª Análise - Mapa das principais regiões de desembarque de escravos
! pip install basedosdados -q
! pip install geobr -q
! pip install pycodestyle -q
! pip install geopandas -q

import basedosdados as bd
import geobr
import pycodestyle
import geopandas as gpd
import shapely

#Quais os principais itinerários escravagistas no Brasil?
#Download do Dataframe
query = '''
SELECT voyage_itinerary_imputed_slave_disembarkation_place AS voyage, COUNT(*) AS voyage_quantity,
SUM(total_disembarked) as total_disembarked
FROM basedosdados.world_slave_voyages_consortium_slave_trade.transatlantic
WHERE voyage_itinerary_imputed_slave_disembarkation_place IS NOT NULL
GROUP BY voyage_itinerary_imputed_slave_disembarkation_place
ORDER BY voyage_quantity DESC
'''

df = bd.read_sql(query, billing_project_id='seu-billing-id')

#Atribuir localidades brasileiras
selected_places = ['Bahia, place unspecified', 'Rio de Janeiro', 'Pernambuco, place unspecified', 
                   'Maranhão', 'St. Vincent, por unspecified', 'Pará', 'Rio de Janeiro province', 
                   'Rio de Janeiro, São Paulo, Santa Catarina', 'São Sebastião', 'Macaé', 'Ilha Grande', 
                   'Santos', 'Paranaguá', 'Cabo de Búzios', 'Rio Grande do Sul, place unspecified', 
                   'Ilha de Marambaia', 'Rio Grande do Norte', 'Cananéia', 'Maricá', 'Maceió', 
                   'Cabo de Búzios', 'Santa Catarina', 'Parati', 'Baía de Botafogo', 'Ubatuba']

# Selecionar Localidades Brasileiras
df['voyage'] = df.loc[df['voyage'].isin(selected_places), 'voyage']

#Substituir valores iguais nas linhas de voyage
df['voyage'] = df['voyage'].replace('Rio de Janeiro province', 'Rio de Janeiro')

#Somatória das linhas
df = df.groupby('voyage').agg({'voyage_quantity': 'sum', 'total_disembarked': 'sum'}).reset_index()

#Atribuição das UF's

# Define um dicionário com as correspondências entre nome do local e sigla da UF
uf_dict = {'Bahia': 'BA', 'Rio de Janeiro': 'RJ', 'Pernambuco': 'PE', 'Maranhão': 'MA',
           'St. Vincent': 'SV', 'Pará': 'PA', 'São Paulo': 'SP', 'Santa Catarina': 'SC',
           'São Sebastião': 'SP', 'Macaé': 'RJ', 'Ilha Grande': 'RJ', 'Santos': 'SP',
           'Paranaguá': 'PR', 'Cabo de Búzios': 'RJ', 'Rio Grande do Sul': 'RS',
           'Ilha de Marambaia': 'RJ', 'Rio Grande do Norte': 'RN', 'Cananéia': 'SP',
           'Maricá': 'RJ', 'Maceió': 'AL', 'Parati': 'RJ',
           'Baía de Botafogo': 'RJ', 'Ubatuba': 'SP'}

# Função para encontrar a UF correspondente a partir do nome do local
def find_uf(local):
    for uf, sigla in uf_dict.items():
        if uf in local:
            return sigla
    return None

#Exclusão de linha que não tem a ver
df.drop(index=df.loc[df['voyage'] == 'Southeast Brazil, port unspecified'].index, inplace=True)

# Criar nova coluna com a UF correspondente
df['uf'] = df['voyage'].apply(find_uf)

#Somatória por UF
df = df.groupby('uf').agg({'voyage_quantity': 'sum', 'total_disembarked': 'sum'}).reset_index()

#Sorteando UF de forma Descendente
df = df.sort_values(by='total_disembarked', ascending =False)
print(df)

regioes = {
    'BA': 'Nordeste',
    'RJ': 'Sudeste',
    'PE': 'Nordeste',
    'MA': 'Nordeste',
    'PA': 'Norte',
    'SP': 'Sudeste',
    'PR': 'Sul',
    'RS': 'Sul',
    'AL': 'Nordeste',
    'SC': 'Sul',
    'RN': 'Nordeste'
}

df['regiao'] = df['uf'].apply(lambda x: regioes[x])
print(df)

df = df.groupby('regiao').agg({'voyage_quantity': 'sum', 'total_disembarked': 'sum'}).reset_index()
print(df)

x = geobr.read_region(2020)

uf = bd.read_table(dataset_id='br_geobr_mapas',
table_id='uf',
billing_project_id="seu-billing-id")

df = pd.merge(df, x, left_on="regiao", right_on="name_region", how="inner")

df.head()

from shapely import wkt

df['geometry'] = df['geometry'].apply(wkt.loads)
df = gpd.GeoDataFrame(df, geometry='geometry')

df.to_csv('slaves.csv', index=False)

#2ª Análise
#Quantos escravos desembarcaram no Brasil?

query= '''
SELECT SUM(total_disembarked) as total_disembarked, 
year_arrival_port_disembarkation, sum(total_embarked) as total_embarked
FROM `basedosdados.world_slave_voyages_consortium_slave_trade.transatlantic`
WHERE flag_vessel = 'Portugal / Brazil'
GROUP BY year_arrival_port_disembarkation
ORDER BY year_arrival_port_disembarkation ASC
'''

df = bd.read_sql(query, billing_project_id='seu-billing-id')

print(df)

df['year_arrival_port_disembarkation'] = df['year_arrival_port_disembarkation'].astype(int)

# Filtrando para o intervalo de 1600 a 1700
# Convertendo a coluna "year_arrival_port_disembarkation" para numérico
df_sec17 = df.query('year_arrival_port_disembarkation >= 1600 and year_arrival_port_disembarkation <= 1700')['total_disembarked'].sum()
df_sec18 = df.query('year_arrival_port_disembarkation >= 1701 and year_arrival_port_disembarkation <= 1800')['total_disembarked'].sum()

print(df_sec17)

print(df_sec18)

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
df.plot(x='year_arrival_port_disembarkation', y='total_disembarked', ax=ax, color='green')
ax.set_title('Total de desembarcados por ano de chegada')
ax.set_xlabel('Ano de chegada')
ax.set_ylabel('Total de desembarcados')
ax.legend(['Total Desembarcados'])
plt.savefig('total_desembarcados.svg', format='svg')
plt.show()

#Save em .svg
ax.figure.savefig("slaves_graphs.svg", transparent=True, format='svg')