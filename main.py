"""
Gerador unificado de Boletins e Relatórios SMED.

Exemplos de uso:
  # Rodar todas as combinações configuradas em config.py
  python main.py --all

  # Nível + formato específico
  python main.py --nivel rede     --formato boletim
  python main.py --nivel regional --formato relatorio
  python main.py --nivel escola   --formato boletim

  # Com filtros opcionais
  python main.py --nivel regional --formato boletim   --regional "SUBURBIO I"
  python main.py --nivel escola   --formato relatorio --regional "CENTRO"
  python main.py --nivel escola   --formato boletim   --escola "ESCOLA MUNICIPAL XAVIER MARQUES"
"""

import argparse

from config import ALL_MODES
from data_loader import load_data
from generator import boletim, relatorio


def dispatch(nivel: str, formato: str, data: dict, regional_filter: str = None, escola_filter: str = None):
    gen = boletim if formato == 'boletim' else relatorio
    if nivel == 'escola':
        gen.gerar_escola(data, regional_filter, escola_filter)
    elif nivel == 'regional':
        gen.gerar_regional(data, regional_filter)
    elif nivel == 'rede':
        gen.gerar_rede(data)


def main():
    parser = argparse.ArgumentParser(
        description='Gerador de Boletins e Relatórios SMED',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--nivel',    choices=['escola', 'regional', 'rede'],  help='Nível de agregação')
    parser.add_argument('--formato',  choices=['boletim', 'relatorio'],        help='Formato de saída')
    parser.add_argument('--regional', metavar='NOME',                          help='Filtrar por regional específica')
    parser.add_argument('--escola',   metavar='NOME',                          help='Filtrar por escola específica (requer --nivel escola)')
    parser.add_argument('--all',      action='store_true', dest='run_all',     help='Executar todos os modos definidos em config.ALL_MODES')

    args = parser.parse_args()

    if args.run_all:
        # Agrupa por formato para carregar os dados apenas uma vez por formato
        formatos_necessarios = dict.fromkeys(fmt for _, fmt in ALL_MODES)
        for formato in formatos_necessarios:
            print(f"\n{'='*60}")
            print(f"Carregando dados para formato: {formato.upper()}")
            print('='*60)
            data = load_data(formato)
            for nivel, fmt in ALL_MODES:
                if fmt != formato:
                    continue
                print(f"\n--- {nivel.upper()} / {formato.upper()} ---")
                dispatch(nivel, formato, data)
    else:
        if not args.nivel or not args.formato:
            parser.error('--nivel e --formato são obrigatórios (ou use --all)')
        if args.escola and args.nivel != 'escola':
            parser.error('--escola só pode ser usado com --nivel escola')

        print(f"Carregando dados para formato: {args.formato.upper()}")
        data = load_data(args.formato)
        dispatch(args.nivel, args.formato, data, args.regional, args.escola)

    print("\nProcesso concluído.")


if __name__ == '__main__':
    main()
