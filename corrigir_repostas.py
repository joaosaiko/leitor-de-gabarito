import json
import sys

# Dicionário com as respostas corretas (exemplo)
respostas_corretas = {
    1: "A", 2: "C", 3: "B", 4: "D", 5: "E",
    6: "A", 7: "B", 8: "D", 9: "C", 10: "E",
    11: "B", 12: "A", 13: "C", 14: "D", 15: "E"
}

def corrigir_prova(arquivo_json):
    with open(arquivo_json, "r") as file:
        respostas_identificadas = json.load(file)

    correcao = {}
    acertos = 0

    for num_questao, resposta_dada in respostas_identificadas.items():
        resposta_correta = respostas_corretas.get(num_questao, "N/A")
        correcao[num_questao] = {
            "resposta_dada": resposta_dada,
            "resposta_correta": resposta_correta,
            "correto": resposta_dada == resposta_correta
        }
        if resposta_dada == resposta_correta:
            acertos += 1

    print("\nCorreção da Prova:")
    for questao, dados in correcao.items():
        print(f"Questão {questao}: Sua resposta: {dados['resposta_dada']} | Correta: {dados['resposta_correta']} | {'✅ Correta' if dados['correto'] else '❌ Errada'}")

    print(f"\nTotal de Acertos: {acertos}/{len(respostas_corretas)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python corrigir_respostas.py <arquivo_json>")
        sys.exit(1)
    
    arquivo_json = sys.argv[1]
    corrigir_prova(arquivo_json)
