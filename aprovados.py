import pandas as pd

from PyPDF2 import PdfReader
import re


re_topicos = re.compile(r'(?<!\d\.)\d+\.\s')
re_sub_topicos = re.compile(r'\d+\.\d+\.')

re_seccional = re.compile(r'\b\d+\.\sOAB\s/\s(\b[A-Za-z]+\b)(.*)')
re_cidade = re.compile(r'\b\d+\.\d\.\s([A-ZÀ-Úa-zà-ú\s]+)\n')
re_aprovado = re.compile(r'(\b\d+\s?\d*\b)\s*\,\s*([A-ZÀ-Úa-zà-ú\s]+)')


# Obtendo a posição de cada tópico
def obter_posicoes_dos_topicos(texto: str) -> list[int]:
    pos_topicos = []

    for topico in re_topicos.finditer(texto):
        pos = topico.span()[0]
        pos_topicos.append(pos)
        
    pos_topicos.append(len(texto) + 1) # final do arquivo
    
    return pos_topicos 


# Obtendo os respectivos sub tópicos

def obter_posicoes_dos_sub_topicos(
        pos_inicial: int, 
        pos_final: int, 
        texto: str
    ) -> list[int]:
    """
    Obtém as posições dos subtópicos de um tópico
    Args.:
        - pos_inicial: posição em que inicia o tópico;
        - pos_final: posição em que inicia o próximo tópico ou o fim do texto;
        - texto: texto extraído do .pdf.
    """
    sub_texto = texto[pos_inicial:pos_final]

    pos_sub_topicos = []
    for sub_topico in re_sub_topicos.finditer(sub_texto):
        pos = sub_topico.span()[0] + pos_inicial
        pos_sub_topicos.append(pos)
    pos_sub_topicos.append(len(sub_texto) + pos_inicial)

    return pos_sub_topicos


# Obtendo os dados dos aprovados

def obter_aprovados_do_sub_topico(
        pos_inicial: int, 
        pos_final: int, 
        texto: str,
        seccional: str
    ) -> list[dict]:
    """
    Obtém os dados dos aprovados para um sub topico
    Args.:
        - pos_inicial: posição em que inicia o sub tópico;
        - pos_final: posição em que inicia o próximo sub tópico ou o fim do texto;
        - texto: texto extraído do .pdf;
        - seccional: seccional em que os sub tópicos estão inseridos.
    """
    sub_texto = texto[pos_inicial:pos_final]
    
    # Cidade de Prova
    cidade_re = re_cidade.search(sub_texto)
    if cidade_re:
        cidade = cidade_re.group(1)
    else:
        cidade = ''

    # Aprovados
    lista_de_pessoas = sub_texto.split('/')

    aprovados = []
    for pessoa in lista_de_pessoas:
        dados_da_pessoa = re_aprovado.search(pessoa.replace('\n', ''))
        if dados_da_pessoa:
            aprovados.append({
                'Seccional': seccional,
                'Cidade de Prova': cidade, 
                'Número de Inscrição': dados_da_pessoa.group(1), 
                'Nome': dados_da_pessoa.group(2).strip()
            })

    return aprovados


# Obter DataFrame dos aprovados
def obter_aprovados(arquivo: str):
    pdf = PdfReader(arquivo)
    texto = ''.join([page.extract_text(0) for page in pdf.pages])

    # Obter posições dos tópicos
    pos_topicos = obter_posicoes_dos_topicos(texto)

    # Por tópico
    aprovados = []
    for idx in range(len(pos_topicos) - 1):
        pos_sub_topicos = obter_posicoes_dos_sub_topicos(
            pos_inicial = pos_topicos[idx],
            pos_final = pos_topicos[idx + 1],
            texto = texto
        )
        seccional_re = re_seccional.search(texto[pos_topicos[idx]:pos_topicos[idx + 1]])
        if seccional_re:
            seccional = seccional_re.group(1)
        else:
            seccional = ''
        for j in range(len(pos_sub_topicos) - 1):
            aprovados_sub = obter_aprovados_do_sub_topico(
                pos_inicial = pos_sub_topicos[j],
                pos_final = pos_sub_topicos[j + 1],
                texto = texto,
                seccional = seccional
            )
            
            aprovados.extend(aprovados_sub)

    # Tratando os dados
    df = pd.DataFrame(aprovados)
    df['Número de Inscrição'] = df['Número de Inscrição'].str.replace(' ', '')
    df['Nome'] = df['Nome'].str.upper()
    df['Cidade de Prova'] = df['Cidade de Prova'].str.strip()
    df['Nome Junto'] = df['Nome'].str.replace(' ', '')

    return df



if __name__ == '__main__':
    import os

    aprovados = obter_aprovados('Resultado Definitivo 1ª Fase OAB 39.pdf')
    print(aprovados)
