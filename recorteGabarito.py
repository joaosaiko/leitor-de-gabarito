import cv2
import numpy as np
import os
import time
import extrairGabarito as exG
from tkinter import Tk, filedialog
import json

PASTA_RECORTES = "recorteGAB"
os.makedirs(PASTA_RECORTES, exist_ok=True)  # Garante que a pasta já exista

PASTA_JSON = "respostasJson"
os.makedirs(PASTA_JSON, exist_ok=True)  # Garante que a pasta já exista

PASTA_CORRECOES = PASTA_JSON
os.makedirs(PASTA_CORRECOES, exist_ok=True)  # Garante que a pasta de correções já exista

# Dicionário com as respostas corretas do gabarito
GABARITO_CORRETO = {
    1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "D", 7: "C", 8: "B", 9: "A", 10: "B",
    11: "C", 12: "D", 13: "E", 14: "D", 15: "C", 16: "A", 17: "A", 18: "A", 19: "A", 20: "A",
    21: "C", 22: "C", 23: "C", 24: "C", 25: "C", 26: "E", 27: "E", 28: "E", 29: "E", 30: "E",
    31: "B", 32: "B", 33: "B", 34: "B", 35: "B", 36: "A", 37: "A", 38: "A", 39: "A", 40: "A",
    41: "C", 42: "C", 43: "C", 44: "C", 45: "C", 46: "B", 47: "A", 48: "B", 49: "C", 50: "B",
    51: "C", 52: "D", 53: "A", 54: "C", 55: "E", 56: "B", 57: "A", 58: "D", 59: "C", 60: "E"
}

def selecionar_imagem():
    """ Abre uma janela para o usuário selecionar a imagem do gabarito. """
    Tk().withdraw()
    arquivo_selecionado = filedialog.askopenfilename(title="Selecione a imagem do gabarito", 
                                                     filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
    if not arquivo_selecionado:
        print("Nenhum arquivo selecionado. Saindo...")
        exit()
    
    print(f"Imagem selecionada: {arquivo_selecionado}")
    return arquivo_selecionado

def encontrar_contornos(imagem_path):
    imagem_colorida = cv2.imread(imagem_path, cv2.IMREAD_COLOR)
    imagem_cinza = cv2.cvtColor(imagem_colorida, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(imagem_cinza, 150, 255, cv2.THRESH_BINARY_INV)
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return imagem_colorida, contornos

def ordenar_contornos_por_colunas(contornos):
    colunas = sorted(contornos, key=lambda c: cv2.boundingRect(c)[0])
    num_colunas = 4
    largura_total = cv2.boundingRect(colunas[-1])[0] - cv2.boundingRect(colunas[0])[0]
    largura_coluna = largura_total // num_colunas
    colunas_ordenadas = [[] for _ in range(num_colunas)]
    
    for contorno in colunas:
        x, _, _, _ = cv2.boundingRect(contorno)
        indice_coluna = (x - cv2.boundingRect(colunas[0])[0]) // largura_coluna
        colunas_ordenadas[min(indice_coluna, num_colunas - 1)].append(contorno)
    
    for i in range(num_colunas):
        colunas_ordenadas[i] = sorted(colunas_ordenadas[i], key=lambda c: cv2.boundingRect(c)[1])
    
    return colunas_ordenadas

def recortar_colunas(imagem_colorida, colunas_ordenadas):
    campos_recortados = []
    margem_esquerda, margem_geral = 5, 10

    for i, coluna in enumerate(colunas_ordenadas):
        for contorno in coluna:
            x, y, w, h = cv2.boundingRect(contorno)
            if w > 50 and h > 50:
                x_inicio, y_inicio = max(x - margem_esquerda, 0), max(y - margem_geral, 0)
                x_fim, y_fim = min(x + w + margem_geral, imagem_colorida.shape[1]), min(y + h + margem_geral, imagem_colorida.shape[0])
                recorte = imagem_colorida[y_inicio:y_fim, x_inicio:x_fim]
                campos_recortados.append((recorte, i + 1))
    
    return campos_recortados

def salvar_recortes(campos_recortados):
    os.makedirs(PASTA_RECORTES, exist_ok=True)
    for idx, (recorte, coluna) in enumerate(campos_recortados, start=1):
        caminho_arquivo = os.path.join(PASTA_RECORTES, f"recorte_coluna{coluna}_{idx}.png")
        cv2.imwrite(caminho_arquivo, recorte)
        print(f"Recorte salvo: {caminho_arquivo}")

def monitorar_pasta():
    """ Monitora continuamente a pasta de recortes e processa novos arquivos. """
    print("Monitoramento iniciado...")
    while True:
        arquivos = [f for f in os.listdir(PASTA_RECORTES) if f.endswith('.png')]
        if arquivos:
            for arquivo in arquivos:
                processar_arquivo(os.path.join(PASTA_RECORTES, arquivo))
            
            corrigir_respostas()

        time.sleep(2)  # Aguarda 2 segundos antes de verificar novamente

def processar_arquivo(imagem_path):
    """ Processa a imagem do gabarito e salva as respostas identificadas em JSON. """
    print(f"Processando: {imagem_path}")
    
    # Carregar imagem
    imagem = cv2.imread(imagem_path)
    imagem = cv2.resize(imagem, (400, 500), interpolation=cv2.INTER_AREA)

    # Extração do gabarito
    gabarito, bbox = exG.extrairMaiorCtn(imagem)
    imgGray = cv2.cvtColor(gabarito, cv2.COLOR_BGR2GRAY)

    # Processamento da imagem
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 0)
    ret, imgTh = cv2.threshold(imgBlur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Ajuste morfológico para eliminar ruídos
    kernel = np.ones((5, 5), np.uint8)
    imgTh = cv2.morphologyEx(imgTh, cv2.MORPH_CLOSE, kernel)
    imgTh = cv2.morphologyEx(imgTh, cv2.MORPH_OPEN, kernel)

    # Verificar respostas
    respostasMarcadas = {}
    num_linhas, num_colunas = 15, 5
    largura_total, altura_total = gabarito.shape[1], gabarito.shape[0]
    largura_quadrado, altura_quadrado = largura_total / num_colunas, altura_total / num_linhas

    for linha in range(num_linhas):
        resposta_marcada = None
        for coluna in range(num_colunas):
            x, y = int(coluna * largura_quadrado), int(linha * altura_quadrado)
            campo = imgTh[y:y + int(altura_quadrado), x:x + int(largura_quadrado)]

            alternativa = chr(65 + coluna)

            # Se a marcação estiver bem preenchida, registra a alternativa
            if verificar_preenchimento(campo):
                resposta_marcada = alternativa

        # Se nenhuma alternativa estiver preenchida corretamente, considerar "N/A"
        if resposta_marcada is None:
            resposta_marcada = "N/A"

        respostasMarcadas[linha + 1] = resposta_marcada

    print(f"Respostas identificadas: {respostasMarcadas}")

    # Criar nome do arquivo JSON com base no nome da imagem
    nome_arquivo_json = os.path.join(PASTA_JSON, f"respostas_{os.path.basename(imagem_path).split('.')[0]}.json")

    # Salvar em JSON
    with open(nome_arquivo_json, "w", encoding="utf-8") as f:
        json.dump(respostasMarcadas, f, indent=4, ensure_ascii=False)

    print(f"Respostas salvas em: {nome_arquivo_json}")

    # Remover a imagem após o processamento
    os.remove(imagem_path)

def verificar_preenchimento(campo):
    """Verifica se a marcação está corretamente preenchida."""
    contornos, _ = cv2.findContours(campo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contornos:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)

        AREA_MIN = 700
        AREA_MAX = 2500

        if AREA_MIN < area < AREA_MAX and w > 10 and h > 10:
            return True
    
    return False

def corrigir_respostas():
    """Compara as respostas dos arquivos JSON gerados com o gabarito correto em blocos de 15 questões."""
    arquivos_json = sorted([f for f in os.listdir(PASTA_JSON) if f.endswith(".json")])  # Ordenar arquivos por nome
    total_arquivos = len(arquivos_json)

    if not arquivos_json:
        print("Nenhum arquivo de resposta encontrado para correção.")
        return

    # Separar o gabarito correto em blocos de 15 em 15
    blocos_gabarito = [dict(list(GABARITO_CORRETO.items())[i:i+15]) for i in range(0, len(GABARITO_CORRETO), 15)]

    # Verifica se o número de arquivos corresponde ao número de blocos gerados
    if len(blocos_gabarito) != total_arquivos:
        print(f"Aviso: O número de arquivos ({total_arquivos}) não corresponde ao número de blocos de 15 ({len(blocos_gabarito)}).")
        print("Isso pode indicar um problema na captura das questões.")
    
    # Processa cada arquivo aplicando o bloco correto do gabarito
    for idx, arquivo in enumerate(arquivos_json):
        caminho_arquivo = os.path.join(PASTA_JSON, arquivo)

        # Carregar respostas do aluno
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            respostas_aluno = json.load(f)

        # Seleciona o bloco correto do gabarito (correspondente ao índice do arquivo)
        bloco_gabarito = blocos_gabarito[idx] if idx < len(blocos_gabarito) else {}

        correcao = {}
        acertos = 0
        erros = 0

        # Garante que a correspondência entre questões e respostas está correta
        for i, (questao, resposta_correta) in enumerate(bloco_gabarito.items(), start=1):
            resposta_aluno = respostas_aluno.get(str(i), "N/A")  # Pegando resposta do aluno
            correta = resposta_aluno == resposta_correta
            
            if correta:
                acertos += 1
            else:
                erros += 1

            correcao[questao] = {
                "resposta_aluno": resposta_aluno,
                "resposta_correta": resposta_correta,
                "correta": correta
            }

        # Criar JSON com a correção
        resultado_correcao = {
            "arquivo_original": arquivo,
            "total_questoes": len(respostas_aluno),
            "acertos": acertos,
            "erros": erros,
            "detalhes": correcao
        }

        # Nome do arquivo corrigido
        nome_arquivo_correcao = os.path.join(PASTA_CORRECOES, f"correcao_{arquivo}")

        # Salvar correção em JSON
        with open(nome_arquivo_correcao, "w", encoding="utf-8") as f:
            json.dump(resultado_correcao, f, indent=4, ensure_ascii=False)

        print(f"Correção salva em: {nome_arquivo_correcao}")


def main():
    imagem_path = selecionar_imagem()
    imagem_colorida, contornos = encontrar_contornos(imagem_path)
    colunas_ordenadas = ordenar_contornos_por_colunas(contornos)
    campos_recortados = recortar_colunas(imagem_colorida, colunas_ordenadas)
    salvar_recortes(campos_recortados)
    
    print("Todos os recortes foram salvos. Iniciando monitoramento automaticamente...")
    monitorar_pasta()

if __name__ == "__main__":
    main()